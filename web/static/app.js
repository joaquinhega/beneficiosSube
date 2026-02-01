let cacheBeneficios = [];

document.addEventListener('DOMContentLoaded', async () => {
    const res = await fetch('/api/beneficios');
    cacheBeneficios = await res.json();
    render(cacheBeneficios);
    document.getElementById('loading').style.display = 'none';

    document.getElementById('searchInput').addEventListener('input', (e) => {
        const t = e.target.value.toLowerCase();
        const filt = cacheBeneficios.filter(b => 
            b.banco.toLowerCase().includes(t) || b.dias_semana.toLowerCase().includes(t)
        );
        render(filt);
    });
});

function render(lista) {
    const grid = document.getElementById('gridBeneficios');
    grid.innerHTML = lista.map(b => `
        <div class="card" style="border-top-color: ${b.color_hex || '#007bff'}">
            <div class="card-header">
                <img src="${b.logo_url}" class="bank-logo">
                <span class="bank-tag" style="color:${b.color_hex}; background:${b.color_hex}22">${b.banco}</span>
                <span class="discount-badge">${b.porcentaje_descuento}%</span>
            </div>
            <div class="card-body">
                <h3 style="color:${b.color_hex}">${b.tipo_transporte}</h3>
                <p><strong>Tope: $</strong>${b.tope_reintegro}</p>
                <p><strong>Días:</strong> ${b.dias_semana}</p>
                <p><strong>Pago:</strong> ${b.metodos_pago}</p>
            </div>
            <div class="card-footer">
                <a href="${b.url_detalle_promo}" target="_blank" class="btn-link" style="color:${b.color_hex}; border-color:${b.color_hex}">Ver Promo</a>
            </div>
        </div>
    `).join('');
}