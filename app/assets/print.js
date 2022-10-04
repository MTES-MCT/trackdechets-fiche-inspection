function resizeForPrinting(e) {
    document.querySelectorAll('.dash-graph').forEach(function (element) {

        const box = element.getBoundingClientRect()
        Plotly.relayout(element, { width: box.width, height: box.height, autosize: true })

    })
}

window.addEventListener('beforeprint', resizeForPrinting)