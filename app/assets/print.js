function resizeForPrinting() {
    $('.dash-graph').each(function () {
        if (this.layout) {
            const box = this.getBoundingClientRect()
            Plotly.relayout(this, { width: box.width, height: box.height })
        }
    })
}

function restoreFromPrinting() {
    $('.dash-graph').each(function () {
        if (this.layout) {
            Plotly.relayout(this, { width: null, height: null, autosize: true })
        }
    })
}

window.addEventListener('beforeprint', resizeForPrinting)
window.addEventListener('afterprint', restoreFromPrinting)
window.matchMedia('print').addListener(function (mql) {
    if (mql.matches) {
        resizeForPrinting()
    } else {
        restoreFromPrinting()
    }
})