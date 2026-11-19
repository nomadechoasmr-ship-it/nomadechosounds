"""Замер ровности звука окнами 400 мс (схема для статей сайта).

python -I tools/measure_400ms.py ФАЙЛ.wav [--win 0.4] [--skip 0] [--dur 0]

Python на этом ПК не открывает пути с кириллицей: сначала cp файла в Temp.

Что считает (окна без перекрытия, по умолчанию 400 мс):
  RMS окна, дБFS   = 10*log10(среднее(L^2, R^2) по окну) — оба канала вместе
  std              = стандартное отклонение RMS окон, дБ
  P95-P5           = размах RMS окон между 5-м и 95-м перцентилем, дБ
  RMS > медиана+6/+10 = сколько окон громче медианы на 6 и 10 дБ
  Пик окна         = max |x| по окну (оба канала), дБFS
  Пик > медиана пиков +6/+10 = короткие удары: капля, щелчок, всплеск
  Корреляция L/R   = Пирсон по всему файлу (не aphasemeter)

Добавлено 2026-11-19 (две колонки таблицы сайта, у которых однозначное определение):
  Баланс L/R, дБ   = 20*log10(RMS левого / RMS правого) по всему отрезку;
                     плюс = левый громче (как "L +3.5 dB" у Mountain Brook)
  Энергия < 40 Гц, % = доля энергии ниже 40 Гц в спектре моно-суммы (L+R)/2,
                     окно Ханна на каждом 400-мс окне, постоянная составляющая
                     (0 Гц) не учитывается
Добавлено 2026-11-19, НОВЫЕ определения (старые для ручья/реки нигде не записаны,
поэтому старые цифры тон-центра и дрейфа надо пересчитать этим же скриптом):
  Тон-центр, Гц    = спектральный центроид моно-суммы по кускам 10 с
                     (25 окон по 400 мс, без 0 Гц); печатаем медиану,
                     P5–P95 и мин–макс по кускам
  Дрейф, дБ        = уровень (RMS) каждой полной минуты отрезка;
                     печатаем std минутных уровней и разницу макс−мин
Добавлено 2026-11-20 (для страницы "какого цвета шум у настоящей воды"):
  Наклон спектра, дБ/окт = средняя спектральная плотность мощности (на 1 Гц)
                     моно-суммы по всем окнам, усреднённая в полосах 1/3 октавы;
                     прямая по МНК через уровни полос от --fmin до --fmax
                     (по умолчанию 100–8000 Гц) против log2(частоты).
                     Эталоны: белый ≈ 0, розовый ≈ −3, коричневый ≈ −6 дБ/окт.
                     Отклонение от прямой (RMS остатков, дБ): если > 1.5 дБ,
                     у звука нет одного "цвета", и это надо писать честно. Печатаем и
                     уровни по октавам — по ним видно, где спектр гнётся.
"""
import argparse, sys
import numpy as np
import soundfile as sf

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("wav")
ap.add_argument("--win", type=float, default=0.4)
ap.add_argument("--skip", type=float, default=0.0, help="пропустить секунд с начала")
ap.add_argument("--dur", type=float, default=0.0, help="взять секунд (0 = до конца)")
ap.add_argument("--fmin", type=float, default=100.0, help="низ полосы для наклона, Гц")
ap.add_argument("--fmax", type=float, default=8000.0, help="верх полосы для наклона, Гц")
a = ap.parse_args()

info = sf.info(a.wav)
sr, ch = info.samplerate, info.channels
n = int(round(a.win * sr))
start = int(a.skip * sr)
stop = info.frames if a.dur <= 0 else min(info.frames, start + int(a.dur * sr))

hann = np.hanning(n)
freqs = np.fft.rfftfreq(n, 1 / sr)
low = (freqs > 0) & (freqs < 40)
band = freqs > 0

rms, pk, pw, fpw = [], [], [], []
sxx = syy = sxy = sx = sy = 0.0
cnt = 0
e_low = e_all = 0.0
spec_sum = np.zeros(len(freqs))
for blk in sf.blocks(a.wav, blocksize=n * 100, start=start, stop=stop,
                     dtype="float64", always_2d=True):
    full = (len(blk) // n) * n          # хвост короче окна отбрасываем
    if full == 0:
        continue
    w = blk[:full].reshape(-1, n, ch)
    p = np.mean(w ** 2, axis=(1, 2))
    pw.extend(p)
    rms.extend(10 * np.log10(np.maximum(p, 1e-20)))
    pk.extend(20 * np.log10(np.maximum(np.max(np.abs(w), axis=(1, 2)), 1e-10)))
    spec = np.abs(np.fft.rfft(w.mean(axis=2) * hann, axis=1)) ** 2
    e_low += spec[:, low].sum(); e_all += spec[:, band].sum()
    spec_sum += spec.sum(axis=0)
    fpw.extend(zip((spec[:, band] * freqs[band]).sum(axis=1), spec[:, band].sum(axis=1)))
    if ch >= 2:
        L, R = blk[:full, 0], blk[:full, 1]
        sx += L.sum(); sy += R.sum(); sxx += (L * L).sum(); syy += (R * R).sum()
        sxy += (L * R).sum(); cnt += len(L)

if not rms:
    sys.exit("Отрезок короче одного окна — нечего мерить.")
rms, pk = np.array(rms), np.array(pk)
med, pmed = np.median(rms), np.median(pk)
p5, p95 = np.percentile(rms, [5, 95])
k = len(rms)

def share(x):
    return f"{x} ({100 * x / k:.1f} %)"

print(f"Файл: {a.wav}")
print(f"{sr} Гц, {ch} кан., отрезок {(stop - start) / sr:.1f} с, окон {k} по {a.win * 1000:.0f} мс")
print(f"RMS окон: медиана {med:.2f} дБFS, std {np.std(rms):.2f} дБ, "
      f"P5 {p5:.2f}, P95 {p95:.2f}, P95-P5 {p95 - p5:.2f} дБ, "
      f"мин {rms.min():.2f}, макс {rms.max():.2f}")
print(f"RMS окна > медиана+6 дБ: {share(int((rms > med + 6).sum()))}, "
      f"> +10 дБ: {share(int((rms > med + 10).sum()))}")
print(f"Пик окон: медиана {pmed:.2f} дБFS, макс {pk.max():.2f}")
print(f"Пик окна > медиана пиков+6 дБ: {share(int((pk > pmed + 6).sum()))}, "
      f"> +10 дБ: {share(int((pk > pmed + 10).sum()))}")
per10 = int(round(10 / a.win)); per60 = int(round(60 / a.win))
fp = np.array(fpw); m = len(fp) // per10
if m:
    c = fp[:m * per10].reshape(m, per10, 2).sum(axis=1)
    cen = c[:, 0] / np.maximum(c[:, 1], 1e-30)
    q5, q95 = np.percentile(cen, [5, 95])
    print(f"Тон-центр (куски 10 с, {m} шт.): медиана {np.median(cen):.0f} Гц, "
          f"P5–P95 {q5:.0f}–{q95:.0f}, мин–макс {cen.min():.0f}–{cen.max():.0f} Гц")
pwa = np.array(pw); mm = len(pwa) // per60
if mm >= 2:
    lv = 10 * np.log10(np.maximum(pwa[:mm * per60].reshape(mm, per60).mean(axis=1), 1e-20))
    print(f"Дрейф (полных минут {mm}): std {np.std(lv):.2f} дБ, макс−мин {lv.max() - lv.min():.2f} дБ")
if e_all > 0:
    print(f"Энергия ниже 40 Гц: {100 * e_low / e_all:.3f} %")
# Наклон спектра: полосы 1/3 октавы, плотность мощности на 1 Гц (среднее по бинам)
centres = 1000 * 2 ** (np.arange(-30, 15) / 3)
lv_b, f_b = [], []
for fc in centres:
    lo, hi = fc / 2 ** (1 / 6), fc * 2 ** (1 / 6)
    if fc < a.fmin * 0.999 or fc > a.fmax * 1.001 or hi > sr / 2:
        continue
    sel = (freqs >= lo) & (freqs < hi)
    if sel.sum() < 2:
        continue
    f_b.append(fc); lv_b.append(10 * np.log10(max(spec_sum[sel].mean(), 1e-30)))
if len(f_b) >= 4:
    x, y = np.log2(f_b), np.array(lv_b)
    slope, icpt = np.polyfit(x, y, 1)
    dev = np.sqrt(np.mean((y - (slope * x + icpt)) ** 2))
    near = min([(0, "белому"), (-3, "розовому"), (-6, "коричневому")], key=lambda t: abs(slope - t[0]))
    print(f"Наклон спектра {f_b[0]:.0f}–{f_b[-1]:.0f} Гц: {slope:+.2f} дБ/окт, отклонение от прямой {dev:.2f} дБ "
          f"(ближе к {near[1]}: {near[0]:+d} дБ/окт; белый 0, розовый −3, коричневый −6)")
    if dev > 1.5:
        print("  Отклонение > 1.5 дБ: спектр не прямая, одного «цвета» у звука нет — смотри уровни по октавам")
    ref = y[np.argmin(np.abs(np.array(f_b) - 1000))]
    octs = [(fc, l) for fc, l in zip(f_b, y) if abs(np.log2(fc / 125) % 1) < 0.01 or abs(np.log2(fc / 125) % 1 - 1) < 0.01]
    print("  Уровни полос относительно 1 кГц, дБ: " +
          ", ".join(f"{fc:.0f} Гц {l - ref:+.1f}" for fc, l in octs))

if cnt:
    cov = sxy / cnt - (sx / cnt) * (sy / cnt)
    vx = sxx / cnt - (sx / cnt) ** 2
    vy = syy / cnt - (sy / cnt) ** 2
    print(f"Корреляция L/R (Пирсон): {cov / np.sqrt(vx * vy):+.3f}")
    print(f"Баланс L/R: {10 * np.log10(sxx / syy):+.2f} дБ (плюс = левый громче)")
