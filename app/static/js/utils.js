/**
 * Utilidades JavaScript - Leal Café
 * Funciones reutilizables para toda la aplicación
 */

// ============================
// FORMATEO DE NÚMEROS Y MONEDA
// ============================

/**
 * Formatear número como moneda mexicana
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(value);
}

/**
 * Formatear número con separadores de miles
 */
function formatNumber(value, decimals = 2) {
    return new Intl.NumberFormat('es-MX', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

/**
 * Parsear string de moneda a número
 */
function parseCurrency(currencyString) {
    return parseFloat(currencyString.replace(/[^0-9.-]+/g, ""));
}

// ============================
// FORMATEO DE FECHAS
// ============================

/**
 * Formatear fecha a formato local
 */
function formatDate(date, format = 'long') {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    const formats = {
        short: { year: 'numeric', month: '2-digit', day: '2-digit' },
        medium: { year: 'numeric', month: 'short', day: 'numeric' },
        long: { year: 'numeric', month: 'long', day: 'numeric' },
        full: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
    };

    return new Intl.DateTimeFormat('es-MX', formats[format] || formats.long).format(dateObj);
}

/**
 * Formatear fecha y hora
 */
function formatDateTime(date) {
    const dateObj = typeof date === 'string' ? new Date(date) : date;

    return new Intl.DateTimeFormat('es-MX', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(dateObj);
}

/**
 * Obtener fecha actual en formato YYYY-MM-DD
 */
function getCurrentDate() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// ============================
// ALERTAS Y NOTIFICACIONES
// ============================

/**
 * Mostrar alerta en la página
 */
function showAlert(message, type = 'info', duration = 5000) {
    const container = document.querySelector('.dashboard-container');
    if (!container) return;

    const icons = {
        success: 'check-circle',
        danger: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.animation = 'slideInDown 0.3s ease-out';
    alert.innerHTML = `
        <i class="fas fa-${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;

    container.insertBefore(alert, container.firstChild);

    if (duration > 0) {
        setTimeout(() => {
            alert.style.animation = 'slideOutUp 0.3s ease-out';
            setTimeout(() => alert.remove(), 300);
        }, duration);
    }
}

/**
 * Mostrar toast notification
 */
function showToast(message, type = 'info') {
    // Crear contenedor si no existe
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
        `;
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        min-width: 300px;
        animation: slideInRight 0.3s ease-out;
    `;
    toast.innerHTML = `<span>${message}</span>`;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================
// VALIDACIÓN DE FORMULARIOS
// ============================

/**
 * Validar email
 */
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validar que un campo no esté vacío
 */
function isNotEmpty(value) {
    return value !== null && value !== undefined && value.trim() !== '';
}

/**
 * Validar que un número esté en rango
 */
function isInRange(value, min, max) {
    const num = parseFloat(value);
    return !isNaN(num) && num >= min && num <= max;
}

/**
 * Validar formulario completo
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const inputs = form.querySelectorAll('[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!isNotEmpty(input.value)) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// ============================
// MANEJO DE TABLAS
// ============================

/**
 * Filtrar tabla por término de búsqueda
 */
function filterTable(tableId, searchTerm) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');

    const term = searchTerm.toLowerCase();

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

/**
 * Ordenar tabla por columna
 */
function sortTable(tableId, columnIndex, ascending = true) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aText = a.cells[columnIndex].textContent.trim();
        const bText = b.cells[columnIndex].textContent.trim();

        const aNum = parseFloat(aText.replace(/[^0-9.-]+/g, ""));
        const bNum = parseFloat(bText.replace(/[^0-9.-]+/g, ""));

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        } else {
            return ascending ? aText.localeCompare(bText) : bText.localeCompare(aText);
        }
    });

    rows.forEach(row => tbody.appendChild(row));
}

// ============================
// FETCH API HELPERS
// ============================

/**
 * Wrapper para fetch con manejo de errores
 */
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en la petición');
        }

        return { success: true, data };

    } catch (error) {
        console.error('Error en fetchAPI:', error);
        return { success: false, error: error.message };
    }
}

/**
 * POST con FormData
 */
async function postFormData(url, formData) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en la petición');
        }

        return { success: true, data };

    } catch (error) {
        console.error('Error en postFormData:', error);
        return { success: false, error: error.message };
    }
}

// ============================
// EXPORTACIÓN A EXCEL
// ============================

/**
 * Exportar tabla a Excel usando ExcelJS
 * Requiere: <script src="https://cdn.jsdelivr.net/npm/exceljs@4.3.0/dist/exceljs.min.js"></script>
 */
async function exportTableToExcel(tableId, fileName = 'datos') {
    if (typeof ExcelJS === 'undefined') {
        console.error('ExcelJS no está cargado');
        showAlert('Error: Librería de exportación no disponible', 'danger');
        return;
    }

    const table = document.getElementById(tableId);
    if (!table) {
        console.error('Tabla no encontrada');
        return;
    }

    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Datos');

    // Obtener headers
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());

    // Configurar columnas
    worksheet.columns = headers.map(header => ({
        header: header,
        key: header.toLowerCase().replace(/\s+/g, '_'),
        width: 20
    }));

    // Estilo de headers
    worksheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } };
    worksheet.getRow(1).fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FF3E2723' }
    };

    // Agregar datos
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const rowData = {};
        const cells = row.querySelectorAll('td');

        cells.forEach((cell, index) => {
            const key = headers[index].toLowerCase().replace(/\s+/g, '_');
            rowData[key] = cell.textContent.trim();
        });

        worksheet.addRow(rowData);
    });

    // Descargar
    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${fileName}_${getCurrentDate()}.xlsx`;
    link.click();

    showToast('Archivo Excel descargado exitosamente', 'success');
}

// ============================
// LOADING SPINNER
// ============================

/**
 * Mostrar overlay de carga
 */
function showLoading(message = 'Cargando...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div style="text-align: center; color: white;">
            <div class="spinner"></div>
            <p style="margin-top: 16px; font-size: 16px;">${message}</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

/**
 * Ocultar overlay de carga
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// ============================
// UTILIDADES GENERALES
// ============================

/**
 * Debounce para eventos
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copiar texto al portapapeles
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copiado al portapapeles', 'success');
    } catch (err) {
        console.error('Error al copiar:', err);
        showToast('Error al copiar', 'danger');
    }
}

/**
 * Confirmar acción con callback
 */
function confirmAction(message, callback) {
    if (window.confirm(message)) {
        callback();
    }
}

// Exportar funciones si se usa como módulo
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatCurrency,
        formatNumber,
        formatDate,
        formatDateTime,
        showAlert,
        showToast,
        isValidEmail,
        validateForm,
        filterTable,
        sortTable,
        fetchAPI,
        postFormData,
        exportTableToExcel,
        showLoading,
        hideLoading,
        debounce,
        copyToClipboard
    };
}
