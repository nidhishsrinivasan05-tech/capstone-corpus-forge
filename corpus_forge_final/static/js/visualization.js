const slider = document.getElementById("countSlider");
const countLabel = document.getElementById("countLabel");
const chart = document.getElementById("chart");

function drawChart() {
    const count = Number(slider.value);
    countLabel.textContent = count;
    chart.innerHTML = "";
    const visible = terms.slice(0, count);
    const maxValue = visible.length > 0 ? visible[0][1] : 1;
    if (visible.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.innerHTML = "<h3>No terms available</h3><p>Upload documents to build a corpus profile.</p>";
        chart.appendChild(empty);
        return;
    }
    visible.forEach(([term, value]) => {
        const row = document.createElement("div");
        row.className = "bar-row";
        const label = document.createElement("div");
        label.className = "bar-label";
        label.textContent = term;
        const track = document.createElement("div");
        track.className = "bar-track";
        const bar = document.createElement("div");
        bar.className = "bar";
        bar.style.setProperty("--bar-width", `${Math.max(4, (value / maxValue) * 100)}%`);
        const number = document.createElement("div");
        number.className = "bar-value";
        number.textContent = value;
        row.appendChild(label);
        track.appendChild(bar);
        row.appendChild(track);
        row.appendChild(number);
        chart.appendChild(row);
    });
}

slider.addEventListener("input", drawChart);
drawChart();
