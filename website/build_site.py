#!/usr/bin/env python3
"""Build the QTLS dataset portal: reads every experiment README and embeds it
so each experiment card opens its own documentation in a reader panel."""
import re, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "src", "dataset_creation_scripts")
OUT  = os.path.join(HERE, "index.html")

SIMS = {6, 7, 8, 9, 10, 15, 16}   # simulation experiments; the rest are measured

folders = sorted(d for d in os.listdir(BASE)
                 if re.match(r"^\d\d_", d) and os.path.isdir(os.path.join(BASE, d)))

experiments = []
for folder in folders:
    num = int(folder[:2])
    path = os.path.join(BASE, folder, "README.md")
    if not os.path.exists(path):
        continue
    md = open(path, encoding="utf-8").read()

    # H1 title
    h1 = ""
    for line in md.splitlines():
        m = re.match(r"^#\s+(.*)", line)
        if m:
            h1 = m.group(1).strip()
            break
    m = re.match(r"Experiment\s+\d+\s*[—\-]\s*(.*)", h1)
    title = m.group(1).strip() if m else h1

    # short description: first plain paragraph after the H1
    desc = ""
    seen_h1 = False
    para = []
    for line in md.splitlines():
        s = line.strip()
        if not seen_h1:
            if s.startswith("# "):
                seen_h1 = True
            continue
        if s == "":
            if para:
                break
            continue
        if s.startswith(("#", ">", "|", "```", "-", "*", "---", "===")):
            if para:
                break
            continue
        para.append(s)
    desc = " ".join(para)
    desc = re.sub(r"\*\*(.+?)\*\*", r"\1", desc)
    desc = re.sub(r"`(.+?)`", r"\1", desc)
    if len(desc) > 185:
        desc = desc[:185].rsplit(" ", 1)[0] + "…"

    experiments.append({
        "num": f"{num:02d}",
        "title": title,
        "desc": desc,
        "badge": "sim" if num in SIMS else "meas",
        "md": md,
    })

readmes = {e["num"]: {"title": e["title"], "badge": e["badge"], "md": e["md"]}
           for e in experiments}

# experiment cards
cards = []
for e in experiments:
    label = "Simulated" if e["badge"] == "sim" else "Measured"
    cards.append(
        f'''<button class="card exp-card reveal" data-exp="{e['num']}" aria-label="Open documentation for experiment {e['num']}">
        <div class="exp-top"><span class="exp-id">EXP · {e['num']}</span><span class="badge {e['badge']}">{label}</span></div>
        <h3>{e['title']}</h3>
        <p>{e['desc']}</p>
        <span class="read-link">Read documentation <span class="arrow">→</span></span>
      </button>''')
cards_html = "\n".join(cards)

n_meas = sum(1 for e in experiments if e["badge"] == "meas")
n_sim  = sum(1 for e in experiments if e["badge"] == "sim")

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QTLS · Coherent Control Dataset</title>
<meta name="description" content="QTLS — an open dataset of measured and simulated two-level-system ring-downs under coherent microwave control.">
<meta name="theme-color" content="#02040A">
<meta property="og:title" content="QTLS · Coherent Control of Two-Level Systems">
<meta property="og:description" content="An open dataset of measured and simulated TLS ring-downs under coherent microwave control.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%23071A33'/><text x='50' y='72' font-size='62' text-anchor='middle' fill='%2300D9FF'>&#9672;</text></svg>">
<style>
  :root{
    --bg-0:#02040A;--bg-1:#071A33;
    --cyan:#00D9FF;--purple:#7657FF;
    --white:#EAF2FF;--soft:#93A6C4;--faint:#5B6B85;
    --glass:rgba(255,255,255,.045);--glass-2:rgba(255,255,255,.06);
    --stroke:rgba(160,196,255,.14);--stroke-hi:rgba(0,217,255,.45);
    --f-head:"Space Grotesk","Sora","Inter",system-ui,-apple-system,Segoe UI,sans-serif;
    --f-body:"Inter",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
    --f-mono:"JetBrains Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
    --maxw:1180px;--radius:20px;--ease:cubic-bezier(.22,.61,.36,1);
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;font-family:var(--f-body);color:var(--white);background:var(--bg-0);line-height:1.6;-webkit-font-smoothing:antialiased;overflow-x:hidden}
  .bg-grad{position:fixed;inset:0;z-index:-3;pointer-events:none;
    background:
      radial-gradient(1200px 800px at 78% -10%, rgba(118,87,255,.16), transparent 60%),
      radial-gradient(1000px 700px at 8% 12%, rgba(0,217,255,.12), transparent 55%),
      radial-gradient(1400px 1000px at 50% 120%, rgba(7,26,51,.9), transparent 70%),
      linear-gradient(180deg,var(--bg-0),#03060F 40%,var(--bg-0));}
  #field{position:fixed;inset:0;z-index:-2;pointer-events:none;opacity:.85}
  .wave{position:fixed;left:-20%;right:-20%;height:60vh;z-index:-2;pointer-events:none;
    background:radial-gradient(closest-side, rgba(0,217,255,.10), transparent 70%);filter:blur(30px);
    animation:drift 26s var(--ease) infinite alternate;}
  .wave.b{top:40%;background:radial-gradient(closest-side, rgba(118,87,255,.10), transparent 70%);animation-duration:34s;animation-delay:-8s}
  @keyframes drift{from{transform:translate3d(-6%,-4%,0)}to{transform:translate3d(8%,6%,0)}}
  .wrap{max-width:var(--maxw);margin:0 auto;padding:0 24px}

  nav{position:fixed;top:0;left:0;right:0;z-index:50;transition:background .4s var(--ease),border-color .4s,backdrop-filter .4s;border-bottom:1px solid transparent}
  nav.scrolled{background:rgba(4,9,20,.62);backdrop-filter:blur(18px) saturate(140%);border-bottom:1px solid var(--stroke)}
  .nav-in{display:flex;align-items:center;justify-content:space-between;height:68px;max-width:var(--maxw);margin:0 auto;padding:0 24px}
  .logo{display:flex;align-items:center;gap:12px;font-family:var(--f-head);font-weight:600;letter-spacing:.02em}
  .logo .mark{width:30px;height:30px;border-radius:9px;display:grid;place-items:center;background:linear-gradient(140deg,rgba(0,217,255,.25),rgba(118,87,255,.25));border:1px solid var(--stroke-hi);box-shadow:0 0 18px rgba(0,217,255,.25) inset;font-size:15px;color:var(--cyan)}
  .logo b{font-size:15px}
  .logo span{color:var(--faint);font-size:11px;font-family:var(--f-mono);letter-spacing:.14em;text-transform:uppercase}
  .nav-links{display:flex;gap:34px;align-items:center}
  .nav-links a{color:var(--soft);text-decoration:none;font-size:14px;transition:color .25s}
  .nav-links a:hover{color:var(--white)}
  .nav-cta{font-family:var(--f-mono);font-size:12.5px;letter-spacing:.06em}

  .btn{display:inline-flex;align-items:center;gap:10px;cursor:pointer;font-family:var(--f-body);font-weight:500;font-size:14.5px;padding:13px 24px;border-radius:14px;text-decoration:none;transition:transform .35s var(--ease),box-shadow .35s,background .35s,border-color .35s;border:1px solid transparent;color:var(--white)}
  .btn:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}
  .btn-primary{background:linear-gradient(120deg,rgba(0,217,255,.92),rgba(0,183,220,.86));color:#02121a;font-weight:600;box-shadow:0 0 0 1px rgba(0,217,255,.4),0 10px 34px -10px rgba(0,217,255,.6)}
  .btn-primary:hover{transform:translateY(-2px);box-shadow:0 0 0 1px rgba(0,217,255,.6),0 16px 44px -8px rgba(0,217,255,.75)}
  .btn-ghost{background:var(--glass);border:1px solid var(--stroke);backdrop-filter:blur(10px)}
  .btn-ghost:hover{transform:translateY(-2px);border-color:var(--stroke-hi);box-shadow:0 10px 30px -12px rgba(0,217,255,.4)}
  .btn .arrow{transition:transform .35s var(--ease)}
  .btn:hover .arrow{transform:translateX(3px)}

  header.hero{position:relative;min-height:100vh;display:flex;align-items:center;padding:120px 0 80px}
  .hero-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:40px;align-items:center;width:100%}
  .eyebrow{display:inline-flex;align-items:center;gap:9px;font-family:var(--f-mono);font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--cyan);padding:7px 14px;border-radius:999px;border:1px solid var(--stroke);background:var(--glass)}
  .eyebrow .dot{width:6px;height:6px;border-radius:50%;background:var(--cyan);box-shadow:0 0 10px var(--cyan);animation:pulse 2.4s infinite}
  @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.7)}}
  h1{font-family:var(--f-head);font-weight:600;font-size:clamp(2.6rem,6vw,4.6rem);line-height:1.02;letter-spacing:-.02em;margin:26px 0 20px;text-wrap:balance;background:linear-gradient(180deg,#fff,#b9d3ff 70%,#7fa8d6);-webkit-background-clip:text;background-clip:text;color:transparent}
  h1 .accent{background:linear-gradient(120deg,var(--cyan),var(--purple));-webkit-background-clip:text;background-clip:text;color:transparent}
  .lede{color:var(--soft);font-size:clamp(1rem,1.4vw,1.18rem);max-width:56ch;margin:0 0 34px}
  .hero-cta{display:flex;gap:14px;flex-wrap:wrap}
  .hero-meta{display:flex;gap:30px;margin-top:40px;flex-wrap:wrap}
  .hero-meta div{display:flex;flex-direction:column;gap:2px}
  .hero-meta b{font-family:var(--f-head);font-size:1.5rem;font-variant-numeric:tabular-nums}
  .hero-meta span{font-family:var(--f-mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}

  .core-stage{position:relative;height:440px;perspective:1000px;display:grid;place-items:center}
  .core{position:relative;width:230px;height:230px;transform-style:preserve-3d;animation:float 9s ease-in-out infinite}
  @keyframes float{0%,100%{transform:translateY(-10px)}50%{transform:translateY(12px)}}
  .nucleus{position:absolute;inset:38%;border-radius:50%;background:radial-gradient(circle at 35% 30%,#eafcff,var(--cyan) 40%,#056b8a 75%,#022834);box-shadow:0 0 40px 6px rgba(0,217,255,.55),0 0 90px 20px rgba(0,217,255,.25);animation:glow 4s ease-in-out infinite}
  @keyframes glow{0%,100%{box-shadow:0 0 40px 6px rgba(0,217,255,.5),0 0 90px 20px rgba(0,217,255,.22)}50%{box-shadow:0 0 54px 10px rgba(118,87,255,.5),0 0 120px 26px rgba(118,87,255,.22)}}
  .ring{position:absolute;inset:0;border-radius:50%;border:1px solid rgba(0,217,255,.35)}
  .ring::after{content:"";position:absolute;top:-4px;left:50%;width:8px;height:8px;border-radius:50%;background:var(--cyan);box-shadow:0 0 12px var(--cyan);transform:translateX(-50%)}
  .r1{animation:spin1 12s linear infinite}.r2{border-color:rgba(118,87,255,.4);animation:spin2 16s linear infinite}.r2::after{background:var(--purple);box-shadow:0 0 12px var(--purple)}.r3{border-color:rgba(160,196,255,.22);animation:spin3 20s linear infinite}
  @keyframes spin1{from{transform:rotateX(74deg) rotateY(0)}to{transform:rotateX(74deg) rotateY(360deg)}}
  @keyframes spin2{from{transform:rotateX(74deg) rotateY(60deg)}to{transform:rotateX(74deg) rotateY(420deg)}}
  @keyframes spin3{from{transform:rotateX(74deg) rotateY(120deg)}to{transform:rotateX(74deg) rotateY(480deg)}}
  .core-glow{position:absolute;inset:-40%;background:radial-gradient(circle,rgba(0,217,255,.18),transparent 60%);filter:blur(20px);z-index:-1}

  section{position:relative;padding:110px 0}
  .sec-head{max-width:660px;margin-bottom:52px}
  .sec-tag{font-family:var(--f-mono);font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--cyan);display:flex;align-items:center;gap:10px;margin-bottom:16px}
  .sec-tag::before{content:"";width:26px;height:1px;background:linear-gradient(90deg,var(--cyan),transparent)}
  h2{font-family:var(--f-head);font-weight:600;font-size:clamp(1.9rem,3.6vw,2.9rem);letter-spacing:-.015em;margin:0 0 16px;text-wrap:balance;line-height:1.08}
  .sec-head p{color:var(--soft);font-size:1.05rem;margin:0}
  .reveal{opacity:0;transform:translateY(28px) scale(.985);filter:blur(6px);transition:opacity .8s var(--ease),transform .8s var(--ease),filter .8s var(--ease)}
  .reveal.in{opacity:1;transform:none;filter:none}

  .grid{display:grid;gap:20px}
  .cols-3{grid-template-columns:repeat(3,1fr)}
  .card{position:relative;background:var(--glass);border:1px solid var(--stroke);border-radius:var(--radius);padding:26px;backdrop-filter:blur(20px);overflow:hidden;transition:transform .5s var(--ease),border-color .5s,box-shadow .5s,background .5s}
  .card::before{content:"";position:absolute;inset:0;border-radius:inherit;padding:1px;background:linear-gradient(140deg,rgba(0,217,255,.5),transparent 40%,transparent 60%,rgba(118,87,255,.4));-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:0;transition:opacity .5s}
  .card:hover{transform:translateY(-6px);border-color:var(--stroke-hi);background:var(--glass-2);box-shadow:0 24px 60px -24px rgba(0,217,255,.35)}
  .card:hover::before{opacity:1}
  .badge{display:inline-flex;align-items:center;gap:7px;font-family:var(--f-mono);font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;padding:5px 10px;border-radius:999px;border:1px solid var(--stroke)}
  .badge.sim{color:var(--cyan);border-color:rgba(0,217,255,.35);background:rgba(0,217,255,.06)}
  .badge.meas{color:var(--purple);border-color:rgba(118,87,255,.4);background:rgba(118,87,255,.07)}

  /* experiment cards (buttons) */
  .exp-card{display:flex;flex-direction:column;text-align:left;cursor:pointer;font:inherit;color:inherit;width:100%}
  .exp-card:focus-visible{outline:2px solid var(--cyan);outline-offset:3px}
  .exp-top{display:flex;justify-content:space-between;align-items:center}
  .exp-id{font-family:var(--f-mono);font-size:11px;color:var(--faint);letter-spacing:.14em}
  .exp-card h3{font-family:var(--f-head);font-weight:600;font-size:1.14rem;margin:16px 0 8px;letter-spacing:-.01em;line-height:1.25}
  .exp-card p{color:var(--soft);font-size:.92rem;margin:0 0 18px;flex:1}
  .read-link{font-family:var(--f-mono);font-size:12px;letter-spacing:.04em;color:var(--cyan);display:inline-flex;align-items:center;gap:8px;margin-top:auto}
  .read-link .arrow{transition:transform .3s var(--ease)}
  .exp-card:hover .read-link .arrow{transform:translateX(4px)}

  .statband{border-top:1px solid var(--stroke);border-bottom:1px solid var(--stroke);background:rgba(255,255,255,.02);backdrop-filter:blur(10px)}
  .statband .wrap{display:grid;grid-template-columns:repeat(4,1fr)}
  .stat{padding:34px 24px;text-align:center;border-right:1px solid rgba(160,196,255,.08)}
  .stat:last-child{border-right:none}
  .stat b{display:block;font-family:var(--f-head);font-size:2.1rem;font-variant-numeric:tabular-nums;background:linear-gradient(120deg,#fff,var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
  .stat span{font-family:var(--f-mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}

  .code{background:rgba(2,6,14,.8);border:1px solid var(--stroke);border-radius:16px;padding:22px 24px;font-family:var(--f-mono);font-size:13px;line-height:1.75;color:var(--soft);overflow-x:auto;white-space:pre}
  .code .c-key{color:var(--purple)}.code .c-str{color:var(--cyan)}.code .c-com{color:var(--faint)}.code .c-fn{color:#8fd9ff}

  footer{border-top:1px solid var(--stroke);padding:64px 0 40px;margin-top:40px;background:rgba(2,6,14,.5)}
  .foot-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;margin-bottom:44px}
  footer h5{font-family:var(--f-head);font-size:1rem;margin:0 0 14px}
  footer .fl{display:flex;flex-direction:column;gap:10px}
  footer .fl a{color:var(--soft);text-decoration:none;font-size:13.5px;transition:.2s;cursor:pointer}
  footer .fl a:hover{color:var(--cyan)}
  .foot-bottom{display:flex;justify-content:space-between;align-items:center;padding-top:26px;border-top:1px solid rgba(160,196,255,.08);color:var(--faint);font-size:12.5px;flex-wrap:wrap;gap:12px}
  .foot-bottom .credit{font-family:var(--f-mono);letter-spacing:.04em}

  /* ─────────── README reader (modal) ─────────── */
  .reader{position:fixed;inset:0;z-index:100;display:none}
  .reader.open{display:block}
  .reader-backdrop{position:absolute;inset:0;background:rgba(2,5,12,.72);backdrop-filter:blur(6px);opacity:0;transition:opacity .35s}
  .reader.open .reader-backdrop{opacity:1}
  .reader-panel{position:absolute;top:50%;left:50%;transform:translate(-50%,-48%) scale(.98);
    width:min(880px,94vw);max-height:88vh;border-radius:22px;overflow:hidden;
    background:linear-gradient(180deg,rgba(7,18,36,.97),rgba(3,8,18,.99));border:1px solid var(--stroke);
    box-shadow:0 50px 130px -40px rgba(0,0,0,.75);opacity:0;transition:transform .4s var(--ease),opacity .4s;
    display:flex;flex-direction:column}
  .reader.open .reader-panel{transform:translate(-50%,-50%) scale(1);opacity:1}
  .reader-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:20px 28px;border-bottom:1px solid var(--stroke);background:rgba(255,255,255,.02);position:sticky;top:0}
  .reader-head .rt{display:flex;align-items:center;gap:12px;min-width:0}
  .reader-head .rt .exp-id{white-space:nowrap}
  .reader-close{background:var(--glass);border:1px solid var(--stroke);color:var(--white);width:38px;height:38px;border-radius:11px;cursor:pointer;font-size:16px;flex:none;transition:.25s}
  .reader-close:hover{border-color:var(--stroke-hi);color:var(--cyan)}
  .reader-body{overflow-y:auto;flex:1;min-height:0;padding:30px 34px 60px}

  /* markdown styling */
  .md-h{font-family:var(--f-head);letter-spacing:-.01em;line-height:1.2;text-wrap:balance}
  h1.md-h{font-size:1.7rem;margin:0 0 6px;background:linear-gradient(120deg,#fff,var(--cyan));-webkit-background-clip:text;background-clip:text;color:transparent}
  h2.md-h{font-size:1.24rem;margin:34px 0 12px;padding-top:22px;border-top:1px solid rgba(160,196,255,.1);color:var(--white)}
  h3.md-h{font-size:1.05rem;margin:24px 0 10px;color:var(--white)}
  .md-p{color:var(--soft);margin:0 0 14px;font-size:.96rem}
  .md-body strong{color:var(--white);font-weight:600}
  .md-body em{color:var(--white);font-style:italic}
  .md-body code{font-family:var(--f-mono);font-size:.85em;background:rgba(0,217,255,.08);border:1px solid rgba(0,217,255,.16);color:#a9e8ff;padding:1px 6px;border-radius:6px}
  .md-body a{color:var(--cyan)}
  .md-pre{background:rgba(2,6,14,.85);border:1px solid var(--stroke);border-radius:12px;padding:16px 18px;overflow-x:auto;margin:0 0 18px}
  .md-pre code{background:none;border:none;padding:0;color:var(--soft);font-size:.82rem;line-height:1.7;white-space:pre}
  .md-quote{border-left:2px solid var(--cyan);background:rgba(0,217,255,.05);border-radius:0 12px 12px 0;padding:6px 18px;margin:0 0 18px}
  .md-quote .md-p:last-child{margin-bottom:0}
  .md-list{color:var(--soft);margin:0 0 16px;padding-left:22px;font-size:.94rem}
  .md-list li{margin:5px 0}
  .md-list li::marker{color:var(--cyan)}
  .md-hr{border:none;border-top:1px solid rgba(160,196,255,.12);margin:26px 0}
  .md-tablewrap{overflow-x:auto;border:1px solid var(--stroke);border-radius:12px;margin:0 0 20px;background:rgba(3,8,18,.5)}
  .md-table{width:100%;border-collapse:collapse;font-size:12.5px;min-width:460px}
  .md-table th,.md-table td{text-align:left;padding:10px 14px;border-bottom:1px solid rgba(160,196,255,.08)}
  .md-table th{font-family:var(--f-mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);font-weight:500}
  .md-table td{color:var(--soft)}
  .md-table tr:last-child td{border-bottom:none}
  .md-table code{font-size:.9em}

  @media(max-width:960px){
    .hero-grid{grid-template-columns:1fr}
    .core-stage{height:340px;order:-1}
    .cols-3{grid-template-columns:repeat(2,1fr)}
    .statband .wrap{grid-template-columns:repeat(2,1fr)}
    .stat:nth-child(2){border-right:none}.stat{border-bottom:1px solid rgba(160,196,255,.08)}
    .foot-grid{grid-template-columns:1fr 1fr}
    .nav-links{display:none}
  }
  @media(max-width:560px){
    section{padding:76px 0}
    .cols-3{grid-template-columns:1fr}
    .foot-grid{grid-template-columns:1fr}
    .reader-body{padding:22px 20px 50px}
  }
  @media(prefers-reduced-motion:reduce){*{animation:none!important;transition-duration:.001ms!important}.reveal{opacity:1;transform:none;filter:none}}
</style>
</head>
<body>

<div class="bg-grad"></div>
<canvas id="field"></canvas>
<div class="wave"></div><div class="wave b"></div>

<nav id="nav">
  <div class="nav-in">
    <div class="logo"><div class="mark">◈</div><div><b>QTLS</b> · <span>Coherent Control</span></div></div>
    <div class="nav-links">
      <a href="#overview">Overview</a>
      <a href="#experiments">Experiments</a>
      <a href="#access">Access</a>
      <a href="#experiments" class="nav-cta" style="color:var(--cyan)">Explore ↗</a>
    </div>
  </div>
</nav>

<header class="hero">
  <div class="wrap hero-grid">
    <div>
      <span class="eyebrow"><span class="dot"></span>Open Dataset · Two-Level Systems</span>
      <h1>Coherent Control of <span class="accent">Two-Level Systems</span></h1>
      <p class="lede">QTLS — a dataset of measured ring-downs and matched numerical simulations of coupled two-level-system defects under pulsed microwave control.</p>
      <div class="hero-cta">
        <a href="#experiments" class="btn btn-primary">Explore experiments <span class="arrow">→</span></a>
        <a href="#access" class="btn btn-ghost">Documentation</a>
      </div>
      <div class="hero-meta">
        <div><b>__NEXP__</b><span>Experiments</span></div>
        <div><b>__NMEAS__</b><span>Measured</span></div>
        <div><b>__NSIM__</b><span>Simulated</span></div>
      </div>
    </div>
    <div class="core-stage">
      <div class="core"><div class="core-glow"></div><div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div><div class="nucleus"></div></div>
    </div>
  </div>
</header>

<div class="statband">
  <div class="wrap">
    <div class="stat"><b>__NEXP__</b><span>Experiments</span></div>
    <div class="stat"><b>120M+</b><span>Long-format rows</span></div>
    <div class="stat"><b>PKL · CSV</b><span>Release formats</span></div>
    <div class="stat"><b>10 mK</b><span>Base temperature</span></div>
  </div>
</div>

<section id="overview">
  <div class="wrap">
    <div class="sec-head reveal">
      <div class="sec-tag">01 — The dataset</div>
      <h2>A single-particle window into the noise of quantum hardware</h2>
      <p>Two-level systems (TLS) are microscopic defects that behave like tiny quantum switches, and a leading source of decoherence in superconducting quantum processors. QTLS packages the raw ring-down measurements and matched numerical simulations that probe how those defects respond to — and can be steered by — shaped microwave drives.</p>
    </div>
    <div class="grid cols-3">
      <div class="card reveal"><div class="badge meas">Measured</div><h3 style="font-family:var(--f-head);font-weight:600;font-size:1.16rem;margin:16px 0 8px">Homodyne ring-downs</h3><p style="color:var(--soft);font-size:.93rem;margin:0">Raw in-phase (I) and quadrature (Q) samples acquired exactly as measured — nothing cropped or post-processed. Magnitude, phase and spectra are all recoverable from I/Q.</p></div>
      <div class="card reveal"><div class="badge sim">Simulated</div><h3 style="font-family:var(--f-head);font-weight:600;font-size:1.16rem;margin:16px 0 8px">Lindblad dynamics</h3><p style="color:var(--soft);font-size:.93rem;margin:0">Numerical evolution of coupled TLS ensembles under a Lindblad master equation, capturing the collective excitation ⟨σ⁺σ⁻⟩ as it rings down after pulsed driving.</p></div>
      <div class="card reveal"><div class="badge">Long format</div><h3 style="font-family:var(--f-head);font-weight:600;font-size:1.16rem;margin:16px 0 8px">One row per sample</h3><p style="color:var(--soft);font-size:.93rem;margin:0">Every dataset is tall and thin — one row per time sample, with the drive settings repeated on each row, and a machine-readable JSON data dictionary alongside.</p></div>
    </div>
  </div>
</section>

<section id="experiments">
  <div class="wrap">
    <div class="sec-head reveal">
      <div class="sec-tag">02 — Experiments</div>
      <h2>Every knob, swept and recorded</h2>
      <p>The full release, in order. Each experiment isolates one control axis and records the complete ring-down at every setting — select any card to open its documentation.</p>
    </div>
    <div class="grid cols-3">
      __CARDS__
    </div>
  </div>
</section>

<section id="access">
  <div class="wrap">
    <div class="sec-head reveal">
      <div class="sec-tag">03 — Access</div>
      <h2>Reproducible, top to bottom</h2>
      <p>Every dataset regenerates from a single deterministic script with a pinned physics module. The data files are rebuilt on demand; the code is the deliverable.</p>
    </div>
    <div class="grid" style="grid-template-columns:1fr 1fr;gap:24px">
      <div class="reveal code"><span class="c-com"># build a simulated dataset (deterministic)</span>
<span class="c-key">python</span> experiment_8_dataset_creation.py --workers 16

<span class="c-com"># load a released table</span>
<span class="c-key">import</span> pickle, pandas <span class="c-key">as</span> pd
<span class="c-key">with</span> <span class="c-fn">open</span>(<span class="c-str">"experiment_8_dataset_long.pkl"</span>, <span class="c-str">"rb"</span>) <span class="c-key">as</span> fh:
    payload = pickle.<span class="c-fn">load</span>(fh)
df = pd.<span class="c-fn">DataFrame</span>(payload[<span class="c-str">"data"</span>], columns=payload[<span class="c-str">"columns"</span>])</div>
      <div class="reveal card" style="display:flex;flex-direction:column;justify-content:center;gap:20px">
        <h3 style="font-family:var(--f-head);font-size:1.3rem;margin:0">Every run is verified</h3>
        <p style="color:var(--soft);margin:0">Stored traces are checked against an independent recomputation from the same physics — a bit-for-bit match, re-run on every build via built-in sanity checks.</p>
        <div style="display:flex;gap:10px;flex-wrap:wrap"><span class="badge sim">diff = 0</span><span class="badge">float32</span><span class="badge meas">seed-locked</span></div>
        <a href="#experiments" class="btn btn-primary" style="align-self:flex-start">Browse experiments <span class="arrow">→</span></a>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <div class="logo" style="margin-bottom:16px"><div class="mark">◈</div><div><b>QTLS</b> · <span>Coherent Control</span></div></div>
        <p style="color:var(--soft);max-width:38ch;font-size:14px">An open dataset of measured and simulated two-level-system ring-downs under coherent microwave control.</p>
      </div>
      <div><h5>Dataset</h5><div class="fl"><a href="#experiments">Experiments</a><a href="#access">Reproducibility</a><a href="#overview">Overview</a></div></div>
      <div><h5>Explore</h5><div class="fl"><a href="#experiments">All 15 experiments</a><a href="#access">Access &amp; code</a></div></div>
    </div>
    <div class="foot-bottom">
      <span class="credit">Uses code &amp; simulation methods from the Fitzpatrick Lab, Dartmouth College.</span>
      <span>QTLS · dark quantum theme</span>
    </div>
  </div>
</footer>

<!-- README reader -->
<div class="reader" id="reader" aria-hidden="true" role="dialog" aria-modal="true">
  <div class="reader-backdrop" data-close></div>
  <div class="reader-panel">
    <div class="reader-head">
      <div class="rt"><span class="exp-id" id="reader-id"></span><span class="badge" id="reader-badge"></span></div>
      <button class="reader-close" data-close aria-label="Close">✕</button>
    </div>
    <div class="reader-body md-body" id="reader-body"></div>
  </div>
</div>

<script id="readmes" type="application/json">__READMES__</script>

<script>
(function(){
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DATA=JSON.parse(document.getElementById('readmes').textContent);

  var nav=document.getElementById('nav');
  var onScroll=function(){nav.classList.toggle('scrolled',window.scrollY>24);};
  onScroll();window.addEventListener('scroll',onScroll,{passive:true});

  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.1,rootMargin:'0px 0px -8% 0px'});
  document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});

  /* ---- markdown renderer ---- */
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function inline(s){
    s=esc(s);
    s=s.replace(/`([^`]+)`/g,function(_,a){return '<code>'+a+'</code>';});
    s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
    s=s.replace(/(^|[^*])\*([^*]+)\*/g,'$1<em>$2</em>');
    s=s.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener">$1</a>');
    return s;
  }
  function render(md){
    var lines=md.replace(/\r/g,'').split('\n'),out=[],i=0;
    function isBreak(l){return /^\s*(#|>|```)/.test(l)||/^\s*(---|\*\*\*|___)\s*$/.test(l)||/^\s*([-*]|\d+\.)\s+/.test(l)||/\|/.test(l);}
    while(i<lines.length){
      var ln=lines[i];
      if(/^```/.test(ln)){var b=[];i++;while(i<lines.length&&!/^```/.test(lines[i])){b.push(lines[i]);i++;}i++;out.push('<pre class="md-pre"><code>'+esc(b.join('\n'))+'</code></pre>');continue;}
      if(/\|/.test(ln)&&i+1<lines.length&&/^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i+1])&&/-/.test(lines[i+1])){
        var head=ln,rows=[];i+=2;
        while(i<lines.length&&/\|/.test(lines[i])&&lines[i].trim()!==''){rows.push(lines[i]);i++;}
        var cells=function(r){r=r.trim().replace(/^\|/,'').replace(/\|$/,'');return r.split('|').map(function(c){return inline(c.trim());});};
        var th=cells(head).map(function(c){return '<th>'+c+'</th>';}).join('');
        var tb=rows.map(function(r){return '<tr>'+cells(r).map(function(c){return '<td>'+c+'</td>';}).join('')+'</tr>';}).join('');
        out.push('<div class="md-tablewrap"><table class="md-table"><thead><tr>'+th+'</tr></thead><tbody>'+tb+'</tbody></table></div>');continue;
      }
      if(/^\s*>/.test(ln)){var b=[];while(i<lines.length&&/^\s*>/.test(lines[i])){b.push(lines[i].replace(/^\s*>\s?/,''));i++;}out.push('<blockquote class="md-quote">'+render(b.join('\n'))+'</blockquote>');continue;}
      var h=/^(#{1,6})\s+(.*)$/.exec(ln);
      if(h){var lv=Math.min(h[1].length,3);out.push('<h'+lv+' class="md-h">'+inline(h[2])+'</h'+lv+'>');i++;continue;}
      if(/^\s*(---|\*\*\*|___)\s*$/.test(ln)){out.push('<hr class="md-hr">');i++;continue;}
      if(/^\s*[-*]\s+/.test(ln)||/^\s*\d+\.\s+/.test(ln)){
        var ord=/^\s*\d+\.\s+/.test(ln),it=[];
        while(i<lines.length&&(/^\s*[-*]\s+/.test(lines[i])||/^\s*\d+\.\s+/.test(lines[i]))){it.push('<li>'+inline(lines[i].replace(/^\s*(?:[-*]|\d+\.)\s+/,''))+'</li>');i++;}
        out.push('<'+(ord?'ol':'ul')+' class="md-list">'+it.join('')+'</'+(ord?'ol':'ul')+'>');continue;
      }
      if(ln.trim()===''){i++;continue;}
      var p=[ln];i++;
      while(i<lines.length&&lines[i].trim()!==''&&!isBreak(lines[i])){p.push(lines[i]);i++;}
      out.push('<p class="md-p">'+inline(p.join(' '))+'</p>');
    }
    return out.join('\n');
  }

  /* ---- reader ---- */
  var reader=document.getElementById('reader');
  var body=document.getElementById('reader-body');
  var rid=document.getElementById('reader-id');
  var rbadge=document.getElementById('reader-badge');
  var lastFocus=null;
  function open(num){
    var e=DATA[num];if(!e)return;
    rid.textContent='EXP · '+num;
    rbadge.textContent=e.badge==='sim'?'Simulated':'Measured';
    rbadge.className='badge '+e.badge;
    body.innerHTML=render(e.md);
    body.scrollTop=0;
    lastFocus=document.activeElement;
    reader.classList.add('open');reader.setAttribute('aria-hidden','false');
    document.body.style.overflow='hidden';
    reader.querySelector('.reader-close').focus();
  }
  function close(){
    reader.classList.remove('open');reader.setAttribute('aria-hidden','true');
    document.body.style.overflow='';
    if(lastFocus)lastFocus.focus();
  }
  document.querySelectorAll('.exp-card').forEach(function(c){
    c.addEventListener('click',function(){open(c.getAttribute('data-exp'));});
  });
  reader.querySelectorAll('[data-close]').forEach(function(x){x.addEventListener('click',close);});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&reader.classList.contains('open'))close();});

  /* ---- particle field ---- */
  var cv=document.getElementById('field');if(!cv)return;
  var ctx=cv.getContext('2d'),parts=[],DPR=Math.min(window.devicePixelRatio||1,1.6);
  function size(){cv.width=innerWidth*DPR;cv.height=innerHeight*DPR;ctx.setTransform(DPR,0,0,DPR,0,0);}
  function build(){parts=[];var n=Math.min(80,Math.round(innerWidth/16));for(var i=0;i<n;i++){parts.push({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:Math.random()*1.6+.4,vx:(Math.random()-.5)*.12,vy:(Math.random()-.5)*.12,p:Math.random()*6.28,c:Math.random()>.5?'0,217,255':'118,87,255'});}}
  function frame(){ctx.clearRect(0,0,innerWidth,innerHeight);for(var i=0;i<parts.length;i++){var a=parts[i];a.x+=a.vx;a.y+=a.vy;a.p+=.01;if(a.x<0)a.x=innerWidth;if(a.x>innerWidth)a.x=0;if(a.y<0)a.y=innerHeight;if(a.y>innerHeight)a.y=0;var tw=(Math.sin(a.p)*.5+.5)*.6+.2;ctx.beginPath();ctx.arc(a.x,a.y,a.r,0,6.28);ctx.fillStyle='rgba('+a.c+','+tw.toFixed(2)+')';ctx.fill();for(var j=i+1;j<parts.length;j++){var b=parts[j],dx=a.x-b.x,dy=a.y-b.y,dd=dx*dx+dy*dy;if(dd<12000){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle='rgba(0,217,255,'+(.05*(1-dd/12000)).toFixed(3)+')';ctx.lineWidth=.6;ctx.stroke();}}}if(!reduce)requestAnimationFrame(frame);}
  function init(){size();build();frame();}
  var rt;window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(init,200);});
  init();
})();
</script>

</body>
</html>
"""

html = (TEMPLATE
        .replace("__CARDS__", cards_html)
        .replace("__READMES__", json.dumps(readmes))
        .replace("__NEXP__", str(len(experiments)))
        .replace("__NMEAS__", str(n_meas))
        .replace("__NSIM__", str(n_sim)))

open(OUT, "w", encoding="utf-8").write(html)
print("wrote", OUT, "-", len(experiments), "experiments,", len(html), "bytes")
