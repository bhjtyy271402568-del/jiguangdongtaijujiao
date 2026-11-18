"""准直镜核算（1064 nm 单模光纤 → 4 mm 平行光，送入 B 方案动态聚焦头）
用法：python 准直镜核算.py  → 打印并写 准直镜核算结果.md
数字来源：λ、入射 4 mm、B 方案 f1/f2 来自 设计/审查/Zemax结果_v0.2_审查.md；
熔石英 n=1.4496 @1064【资料：Malitson 色散式】；MFD 14/20 μm 为常见单模 300 W 光纤【假设，待激光器规格书确认】。
"""
import math
lam = 1.064e-3          # mm
n = 1.4496              # 熔石英 @1064
CT = 3.0                # 镜片中心厚 mm【假设】
W_IN = 2.0              # 动聚焦头要求的入射 1/e² 半径 mm（直径 4 mm）

def seq(f, orient):
    R = (n - 1) * f
    if orient == '平面朝光纤':
        return lambda s: [('p', s), ('s', s + CT, -R)]
    return lambda s: [('s', s, R), ('p', s + CT)]

def run(f, orient, s, h0):
    p = [0.0, 0.0]; d = [s, h0]; L = math.hypot(*d); d = [d[0]/L, d[1]/L]
    ns = [1, n, 1]
    for i, S in enumerate(seq(f, orient)(s)):
        if S[0] == 'p':
            t = (S[1]-p[0])/d[0]; p = [p[0]+t*d[0], p[1]+t*d[1]]; m = [-1, 0]
        else:
            Rr = S[2]; cx = S[1]+Rr; ox, oy = p[0]-cx, p[1]
            b = ox*d[0]+oy*d[1]; c = ox*ox+oy*oy-Rr*Rr; D = math.sqrt(b*b-c)
            t = (-b-D) if Rr > 0 else (-b+D)
            p = [p[0]+t*d[0], p[1]+t*d[1]]; m = [(p[0]-cx)/abs(Rr), p[1]/abs(Rr)]
        cs = -(d[0]*m[0]+d[1]*m[1])
        if cs < 0: m = [-m[0], -m[1]]; cs = -cs
        e = ns[i]/ns[i+1]; k = 1-e*e*(1-cs*cs); q = e*cs-math.sqrt(k)
        d = [e*d[0]+q*m[0], e*d[1]+q*m[1]]
    return p, d

def design(f, orient):
    lo, hi = 1.0, 2*f
    for _ in range(80):          # 找“近轴光出射平行”的光纤距离
        mid = (lo+hi)/2; _, d = run(f, orient, mid, 1e-3)
        if d[1] > 0: lo = mid    # 还在发散 → 光纤离镜片太近
        else: hi = mid
    s = (lo+hi)/2
    H, W = [0.0], [0.0]
    for i in range(1, 121):      # 追到出射高 3 mm（1.5 倍光束半径）
        _, d0 = run(f, orient, s, 1e-3)
        p, d = run(f, orient, s, 3.0*i/120*s/f)
        W.append(W[-1] + (d[1]/d[0])*(p[1]-H[-1])); H.append(p[1])
    ws, xs, ys = [], [], []
    for h, w in zip(H[1:], W[1:]):
        g = math.exp(-2*(h/W_IN)**2)*h; ws.append(g); xs.append(h*h); ys.append(w)
    sw = sum(ws); mx = sum(a*b for a, b in zip(ws, xs))/sw; my = sum(a*b for a, b in zip(ws, ys))/sw
    k = sum(a*(x-mx)*(y-my) for a, x, y in zip(ws, xs, ys))/sum(a*(x-mx)**2 for a, x in zip(ws, xs))
    rms = math.sqrt(sum(a*(y-my-k*(x-mx))**2 for a, x, y in zip(ws, xs, ys))/sw)/lam
    return s, rms

# B 方案近轴：动镜 f1、物镜 f2（审查 v0.2）
F1, F2 = -20.47, 90.0
def gap_for(L, V_in=0.0):
    """入射光发散度 V_in（1/mm，正=发散）时，聚焦到 L 所需的两镜间距（近轴光线追迹）"""
    lo, hi = 40.0, 140.0
    for _ in range(80):
        d = (lo+hi)/2
        y, u = 1.0, V_in           # 高 1 mm 的光线，发散角 = 高 × 发散度
        u -= y/F1; y += d*u; u -= y/F2
        v = -y/u if u < 0 else 1e12   # 物镜后焦点距离
        if v > L: lo = d               # 焦点太远 → 两镜再拉开
        else: hi = d
    return (lo+hi)/2

out = ['# 准直镜核算结果（由 准直镜核算.py 生成）', '']
out.append('## 1. 焦距窗口：光纤 MFD → 准直镜焦距')
out.append('| 光纤 MFD | 出光半角（1/e²） | 出 3.5 mm 需 f | 出 4 mm 需 f | 出 5 mm 需 f |'); out.append('|---|---|---|---|---|')
for mfd in (10, 14, 20, 25):
    th = lam/(math.pi*mfd/2e3)
    out.append(f'| {mfd} μm | {th*1e3:.1f} mrad | {1.75/th:.0f} mm | {2/th:.1f} mm | {2.5/th:.0f} mm |')
out += ['', '## 2. 熔石英平凸单片的像差（高斯加权 RMS 波前，已去掉离焦）',
        '| f | 朝向 | 光纤到镜面距离 | RMS 波前 |', '|---|---|---|---|']
for f in (40, 50, 60):
    for o in ('平面朝光纤', '凸面朝光纤'):
        s, r = design(f, o); out.append(f'| {f} mm | {o} | {s:.2f} mm | {r:.3f} λ |')
out += ['', '## 3. 装调公差 → 对系统的影响（以 f = 40 mm 为例）']
f = 40.0
for dx in (0.005, 0.01, 0.02):
    a = dx/f; out.append(f'- 光纤横向偏 {dx*1e3:.0f} μm → 准直光歪 {a*1e3:.2f} mrad → 经 ≈4.5× 扩束后 {a/4.5*1e3:.3f} mrad → 10 m 处光点偏 {a/4.5*1e4:.1f} mm（固定偏差，可标定）')
g0 = {L: gap_for(L) for L in (1000, 10000)}
for dz in (0.02, 0.05, 0.1):
    V = dz/f**2     # 光纤往镜片靠近 dz → 出射略发散（反方向则符号相反、量级相同）
    d1 = gap_for(1000, V)-g0[1000]; d10 = gap_for(10000, V)-g0[10000]
    out.append(f'- 光纤轴向偏 {dz*1e3:.0f} μm → 准直光“虚光源”在 {f*f/dz/1000:.0f} m 外 → 动镜补偿：1 m 处 {d1*1e3:+.0f} μm、10 m 处 {d10*1e3:+.0f} μm')
out.append(f'- 参考：B 方案两镜间距 1 m {g0[1000]:.2f} mm、10 m {g0[10000]:.2f} mm（近轴）')
out += ['', '## 4. 镜片上的功率密度', f'- 300 W、1/e² 半径 2 mm：峰值 {2*300/(math.pi*0.2**2)/1000:.1f} kW/cm²']
txt = '\n'.join(out); print(txt)
open(__file__.replace('.py', '结果.md'), 'w', encoding='utf-8').write(txt + '\n')
