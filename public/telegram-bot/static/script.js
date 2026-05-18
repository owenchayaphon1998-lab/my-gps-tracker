function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    if(tab === 'check') {
        document.getElementById('check-tab').classList.add('active');
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
    } else if (tab === 'scammer') {
        document.getElementById('scammer-tab').classList.add('active');
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
    } else if (tab === 'list') {
        document.getElementById('list-tab').classList.add('active');
        document.querySelectorAll('.tab-btn')[2].classList.add('active');
        fetchCustomers();
    } else {
        document.getElementById('scammerlist-tab').classList.add('active');
        document.querySelectorAll('.tab-btn')[3].classList.add('active');
        fetchScammers();
    }
}

function showLoading(btnId) {
    const btn = document.getElementById(btnId);
    btn.disabled = true;
    btn.querySelector('.btn-text').classList.add('hidden');
    btn.querySelector('.spinner').classList.remove('hidden');
}

function hideLoading(btnId) {
    const btn = document.getElementById(btnId);
    btn.disabled = false;
    btn.querySelector('.btn-text').classList.remove('hidden');
    btn.querySelector('.spinner').classList.add('hidden');
}

function showResult(boxId, type, message) {
    const box = document.getElementById(boxId);
    box.className = `result-box ${type}`;
    box.innerHTML = message;
}

async function checkCustomer() {
    const nameInput = document.getElementById('customer-name');
    const name = nameInput.value.trim();
    if(!name) {
        showResult('check-result', 'danger', '❌ กรุณากรอกชื่อ-นามสกุล');
        return;
    }

    showLoading('btn-check');
    try {
        const res = await fetch('/api/check_customer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        const data = await res.json();
        
        if(data.is_scammer) {
            showResult('check-result', 'danger', data.message);
        } else if(data.is_duplicate) {
            showResult('check-result', 'warning', data.message);
        } else if(data.success) {
            showResult('check-result', 'success', data.message);
            nameInput.value = ''; // clear
        } else {
            showResult('check-result', 'danger', data.message);
        }
    } catch(err) {
        showResult('check-result', 'danger', '❌ เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว');
    }
    hideLoading('btn-check');
}

async function addScammer() {
    const nameInput = document.getElementById('scam-name');
    const bankInput = document.getElementById('scam-bank');
    const descInput = document.getElementById('scam-desc');
    
    const name = nameInput.value.trim();
    const bank = bankInput.value.trim();
    const desc = descInput.value.trim();

    if(!name || !desc) {
        showResult('scam-result', 'danger', '❌ กรุณากรอกชื่อและพฤติกรรมให้ครบ');
        return;
    }

    showLoading('btn-scammer');
    try {
        const res = await fetch('/api/add_scammer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, bank, desc})
        });
        const data = await res.json();
        
        if(data.success) {
            showResult('scam-result', 'success', data.message);
            nameInput.value = ''; bankInput.value = ''; descInput.value = '';
        } else {
            showResult('scam-result', 'danger', data.message);
        }
    } catch(err) {
        showResult('scam-result', 'danger', '❌ เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว');
    }
    hideLoading('btn-scammer');
}

async function fetchCustomers() {
    const container = document.getElementById('customer-list-container');
    container.innerHTML = '<div style="text-align: center; color: #a0aec0;">กำลังโหลด...</div>';
    
    try {
        const res = await fetch('/api/customers');
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('customer-count').innerText = `( ${data.customers.length} คน )`;
            if (data.customers.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #a0aec0;">ยังไม่มีรายชื่อลูกค้า</div>';
                return;
            }
            
            let html = '<ul id="customer-ul" class="customer-list">';
            data.customers.forEach((c, index) => {
                html += `
                <li class="customer-item">
                    <div class="customer-info">
                        <span class="customer-number">${index + 1}.</span>
                        <span class="customer-name">${c.name}</span>
                        <span class="customer-date">${c.date}</span>
                    </div>
                    <button class="delete-btn" onclick="deleteCustomer('${c.name}')">🗑️</button>
                </li>`;
            });
            html += '</ul>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div style="text-align: center; color: #ef4444;">โหลดข้อมูลล้มเหลว</div>';
        }
    } catch(err) {
        container.innerHTML = '<div style="text-align: center; color: #ef4444;">เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว</div>';
    }
}

async function deleteCustomer(name) {
    if(!confirm(`ยืนยันการลบรายชื่อลูกค้า: ${name} ?`)) return;
    
    try {
        const res = await fetch('/api/delete_customer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        const data = await res.json();
        if(data.success) {
            fetchCustomers();
        } else {
            alert('ลบข้อมูลล้มเหลว');
        }
    } catch(err) {
        alert('เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว');
    }
}

async function fetchScammers() {
    const container = document.getElementById('scammer-list-container');
    container.innerHTML = '<div style="text-align: center; color: #a0aec0;">กำลังโหลด...</div>';
    
    try {
        const res = await fetch('/api/scammers');
        const data = await res.json();
        
        if (data.success) {
            document.getElementById('scammer-count').innerText = `( ${data.scammers.length} คน )`;
            if (data.scammers.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #a0aec0;">ยังไม่มีรายชื่อมิจฉาชีพ</div>';
                return;
            }
            
            let html = '<ul id="scammer-ul" class="customer-list">';
            data.scammers.forEach((c, index) => {
                html += `
                <li class="customer-item">
                    <div class="customer-info">
                        <span class="customer-number">${index + 1}.</span>
                        <span class="customer-name">${c.name}</span>
                        <span class="customer-date">บัญชี: ${c.bank} | ${c.desc}</span>
                    </div>
                    <button class="delete-btn" onclick="deleteScammer('${c.name}')">🗑️</button>
                </li>`;
            });
            html += '</ul>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div style="text-align: center; color: #ef4444;">โหลดข้อมูลล้มเหลว</div>';
        }
    } catch(err) {
        container.innerHTML = '<div style="text-align: center; color: #ef4444;">เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว</div>';
    }
}

async function deleteScammer(name) {
    if(!confirm(`ยืนยันการลบมิจฉาชีพ: ${name} ?\n(รายชื่อนี้จะถูกลบออกจาก Blacklist)`)) return;
    
    try {
        const res = await fetch('/api/delete_scammer', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        const data = await res.json();
        if(data.success) {
            fetchScammers();
        } else {
            alert('ลบข้อมูลล้มเหลว: ' + (data.message || ''));
        }
    } catch(err) {
        alert('เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว');
    }
}

function filterList(inputId, listId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const ul = document.getElementById(listId);
    if (!ul) return;
    
    const li = ul.getElementsByTagName('li');
    for (let i = 0; i < li.length; i++) {
        const nameSpan = li[i].querySelector('.customer-name');
        if (nameSpan) {
            const txtValue = nameSpan.textContent || nameSpan.innerText;
            if (txtValue.toLowerCase().indexOf(filter) > -1) {
                li[i].style.display = "";
            } else {
                li[i].style.display = "none";
            }
        }       
    }
}
