// fpgaConvNet optimisation visualiser.
// Steps through the 40 design points the optimiser visited for LeNet on a ZedBoard.
// Data: log/<i>.json (performance and resources) and vis/<i>.dot (hardware graph).
(function () {
  // load the Graphviz WebAssembly binary from this site rather than a CDN
  const hpcc = window['@hpcc-js/wasm'];
  if (hpcc && hpcc.wasmFolder) hpcc.wasmFolder(new URL('fpgaconvnet/wasm', location.href).href);
  const N = 40;
  const slider = document.getElementById("design-slide");
  const label = document.getElementById("point-label");
  const playBtn = document.getElementById("play-btn");
  const graphEl = document.getElementById("graph");
  const wrapper = document.getElementById("graph-wrapper");
  const readThroughput = document.getElementById("read-throughput");
  const readLatency = document.getElementById("read-latency");

  const css = getComputedStyle(document.documentElement);
  const textColor = css.getPropertyValue("--fg").trim() || "#14181f";
  const gridColor = css.getPropertyValue("--line").trim() || "#e1e5ec";
  Chart.defaults.color = textColor;
  Chart.defaults.borderColor = gridColor;

  const logs = new Array(N);
  const dotCache = new Map();

  const getJSON = (url) => fetch(url).then((r) => r.json());
  const getText = (url) => {
    if (!dotCache.has(url)) dotCache.set(url, fetch(url).then((r) => r.text()));
    return dotCache.get(url);
  };

  // charts
  const rscChart = new Chart(document.getElementById("rscChart").getContext("2d"), {
    type: "bar",
    data: {
      labels: ["LUT", "FF", "DSP", "BRAM"],
      datasets: [{
        data: [0, 0, 0, 0],
        borderColor: ["rgb(255,99,132)", "rgb(54,162,235)", "rgb(153,102,255)", "rgb(255,159,64)"],
        backgroundColor: ["rgba(255,99,132,.6)", "rgba(54,162,235,.6)", "rgba(153,102,255,.6)", "rgba(255,159,64,.6)"],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      indexAxis: "y",
      scales: { x: { beginAtZero: true, max: 100, title: { display: true, text: "Resource usage (%)" } } },
      plugins: { legend: { display: false } }
    }
  });

  const perfChart = new Chart(document.getElementById("perfChart").getContext("2d"), {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "Throughput", data: [], borderColor: "rgb(255,99,132)", backgroundColor: "rgba(255,99,132,.6)", yAxisID: "y" },
        { label: "Latency", data: [], borderColor: "rgb(54,162,235)", backgroundColor: "rgba(54,162,235,.6)", yAxisID: "y1" }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { title: { display: true, text: "Design point index" } },
        y: { type: "linear", position: "left", beginAtZero: true, title: { display: true, text: "Throughput (img/s)" } },
        y1: { type: "linear", position: "right", beginAtZero: true, title: { display: true, text: "Latency (s/batch)" }, grid: { drawOnChartArea: false } }
      }
    }
  });

  // hardware graph
  // layout on the main thread so it uses the wasm hosted on this site (no CDN worker)
  const graphviz = d3.select("#graph").graphviz({ useWorker: false })
    .logEvents(false)
    .transition(() => d3.transition("main").ease(d3.easeLinear).delay(20).duration(500))
    .tweenShapes(false)
    .tweenPaths(false)
    .zoomScaleExtent([0.05, 100]);

  let rendering = false;
  let pending = null;
  function renderGraph(i) {
    if (rendering) { pending = i; return; }
    rendering = true;
    getText("fpgaconvnet/vis/" + i + ".dot").then((dot) => {
      graphviz
        .fit(true)
        .width(wrapper.clientWidth - 5)
        .height(wrapper.clientHeight - 5)
        .renderDot(dot)
        .on("end", () => {
          rendering = false;
          if (pending !== null) { const p = pending; pending = null; renderGraph(p); }
        });
    }).catch(() => { rendering = false; });
  }

  function show(i) {
    i = Number(i);
    slider.value = i;
    label.textContent = "Design point " + i + " of " + (N - 1);
    const log = logs[i];
    if (log) {
      rscChart.data.datasets[0].data = [log.resource.LUT, log.resource.FF, log.resource.DSP, log.resource.BRAM];
      rscChart.update();
      readThroughput.textContent = log.throughput.toFixed(1) + " img/s";
      readLatency.textContent = log.latency.toFixed(2) + " s/batch";
    }
    const active = [{ datasetIndex: 0, index: i }, { datasetIndex: 1, index: i }];
    perfChart.setActiveElements(active);
    perfChart.tooltip.setActiveElements(active, { x: 0, y: 0 });
    perfChart.update();
    renderGraph(i);
  }

  // play / pause
  let timer = null;
  function stop() { clearInterval(timer); timer = null; playBtn.textContent = "Play"; }
  function play() {
    if (Number(slider.value) >= N - 1) show(0);
    playBtn.textContent = "Pause";
    timer = setInterval(() => {
      const next = Number(slider.value) + 1;
      if (next >= N) { stop(); return; }
      show(next);
    }, 1200);
  }
  playBtn.addEventListener("click", () => (timer ? stop() : play()));
  slider.addEventListener("input", () => { if (timer) stop(); show(slider.value); });

  // load all metrics, then initialise
  Promise.all(Array.from({ length: N }, (_, i) => getJSON("fpgaconvnet/log/" + i + ".json"))).then((all) => {
    all.forEach((l, i) => (logs[i] = l));
    perfChart.data.labels = all.map((_, i) => String(i));
    perfChart.data.datasets[0].data = all.map((l) => l.throughput);
    perfChart.data.datasets[1].data = all.map((l) => l.latency);
    perfChart.update();
    show(0);
  });
})();
