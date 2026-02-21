// ================= ELEMENTS =================
const table = document.getElementById("table");
const totalEl = document.getElementById("total");
const totalPureEl = document.getElementById("totalPure");
const branchSelect = document.getElementById("branch");

// ================= LOAD TABLE =================
async function loadTable() {
    const branch = branchSelect.value;
    const res = await fetch(`/get?branch=${branch}`);
    const data = await res.json();

    // Clear existing rows
    while (table.rows.length > 1) table.deleteRow(1);

    let totalAmount = 0, totalPure = 0;

    data.forEach(d => {
        let row = table.insertRow();
        row.insertCell(0).innerText = d[1]; // Name
        row.insertCell(1).innerText = d[2]; // Phone
        row.insertCell(2).innerText = d[3]; // Grams
        row.insertCell(3).innerText = d[4]; // %
        row.insertCell(4).innerText = d[5]; // Rate
        row.insertCell(5).innerText = d[6]; // Pure
        row.insertCell(6).innerText = d[7]; // Total

        let actions = row.insertCell(7);
        actions.innerHTML = `<button onclick="deleteRowDB(${d[0]})">Delete</button>
                             <button onclick="printReceipt(${d[0]})">Print</button>`;

        totalAmount += Number(d[7]);
        totalPure += Number(d[6]);
    });

    totalEl.innerText = totalAmount.toLocaleString();
    totalPureEl.innerText = totalPure.toLocaleString();
}

// ================= ADD ENTRY =================
async function addItem() {
    const data = {
        name: document.getElementById("name").value,
        phone: document.getElementById("phone").value,
        grams: parseFloat(document.getElementById("grams").value),
        percent: parseFloat(document.getElementById("percent").value),
        rate: parseFloat(document.getElementById("rate").value),
        branch: branchSelect.value
    };
    data.pure = data.grams * (data.percent / 100);
    data.total = data.pure * data.rate;

    await fetch("/add", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    loadTable();
    clearInputs();
}

// ================= DELETE ROWS =================
async function deleteRowDB(id) {
    if (!confirm("Delete this entry?")) return;
    await fetch(`/delete/${id}`, { method: "DELETE" });
    loadTable();
}

async function deleteAllRows() {
    if (!confirm("Delete ALL entries?")) return;
    await fetch("/delete_all", { method: "POST" });
    loadTable();
}

// ================= CLEAR INPUTS =================
function clearInputs() {
    ["name", "phone", "grams", "percent", "rate"].forEach(id => {
        document.getElementById(id).value = "";
    });
}

// ================= PRINT SINGLE RECEIPT =================
function printReceipt(id) {
    fetch(`/get?branch=${branchSelect.value}`)
        .then(r => r.json())
        .then(data => {
            const row = data.find(x => x[0] === id);
            if (!row) return;

            let w = window.open("", "_blank");
            w.document.write(`
                <html>
                <head>
                    <title>Receipt</title>
                    <style>
                        body { font-family: monospace; width: 300px; margin: 0; padding: 10px; }
                        h2 { text-align: center; margin: 5px 0; }
                        .line { border-bottom: 1px dashed #000; margin: 5px 0; }
                        p { margin: 2px 0; }
                        .total { font-weight: bold; }
                        @media print { body { width: auto; } button { display: none; } }
                    </style>
                </head>
                <body>
                    <h2>GOLD POS RECEIPT</h2>
                    <div class="line"></div>
                    <p><strong>Name:</strong> ${row[1]}</p>
                    <p><strong>Phone:</strong> ${row[2]}</p>
                    <p><strong>Branch:</strong> ${row[8]}</p>
                    <div class="line"></div>
                    <p><strong>Weight:</strong> ${row[3]} g</p>
                    <p><strong>Purity:</strong> ${row[4]} %</p>
                    <p><strong>Pure Gold:</strong> ${row[6]} g</p>
                    <p><strong>Rate:</strong> ${row[5]} KES</p>
                    <div class="line"></div>
                    <p class="total"><strong>Total:</strong> ${row[7]} KES</p>
                    <div class="line"></div>
                    <p style="text-align:center;">Thank you for your purchase!</p>
                </body>
                </html>
            `);
            w.document.close();
            w.print();
        });
}

// ================= PRINT DASHBOARD =================
function printDashboard() {
    let w = window.open("", "_blank");
    w.document.write(document.querySelector(".main").innerHTML);
    w.print();
}

// ================= EXPORT EXCEL =================
function exportExcel() {
    window.open("/export", "_blank");
}

// ================= LOAD REPORT =================
async function loadReport(period) {
    await openPrintView(period);
}

// ================= PRINT FULL REPORT (INCLUSIVE OF ALL FIELDS) =================
async function openPrintView(period = "all") {
    let url = `/report/${period}?branch=${branchSelect.value}`;
    let title = `Gold POS ${period.charAt(0).toUpperCase() + period.slice(1)} Report`;

    try {
        const res = await fetch(url);
        const data = await res.json();

        let w = window.open("", "_blank");
        let content = `
            <html>
            <head>
                <title>${title}</title>
                <style>
                    body { font-family: monospace; width: 350px; margin:0; padding:10px; }
                    h2 { text-align:center; margin:5px 0; }
                    .line { border-bottom:1px dashed #000; margin:5px 0; }
                    p { margin:2px 0; }
                    .total { font-weight:bold; }
                </style>
            </head>
            <body>
                <h2>${title}</h2>
                <div class="line"></div>
        `;

        data.forEach(row => {
            content += `
                <p><strong>Name:</strong> ${row[1]}</p>
                <p><strong>Phone:</strong> ${row[2]}</p>
                <p><strong>Branch:</strong> ${row[3]}</p>
                <p><strong>Weight:</strong> ${row[4]} g | Purity: ${row[5]}%</p>
                <p><strong>Pure Gold:</strong> ${row[6]} g | Rate: ${row[7]} KES</p>
                <p class="total"><strong>Total:</strong> ${row[8]} KES</p>
                <div class="line"></div>
            `;
        });

        content += `<p style="text-align:center;">Thank you!</p></body></html>`;
        w.document.write(content);
        w.document.close();
        w.print();
    } catch (err) {
        console.error(err);
        alert("Failed to load report data.");
    }
}

// ================= INITIAL LOAD =================
window.onload = () => {
    loadTable();
};