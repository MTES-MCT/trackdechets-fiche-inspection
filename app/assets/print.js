function relayoutPlotly() {
    document.querySelectorAll('.dash-graph').forEach(function (element) {

        const box = element.getBoundingClientRect()
        Plotly.relayout(element.getElementsByClassName("js-plotly-plot")[0], { width: box.width, height: box.height, autosize: true })

    })
}

function resizeForPrinting(e) {
    console.log('Before print');
    const layoutContainer = document.querySelector("#layout-container")
    layoutContainer.className = "printing"

    relayoutPlotly()
    //setTimeout(print, 500)

}

function resetLayout() {
    const layoutContainer = document.querySelector("#layout-container")
    layoutContainer.className = ""
    setTimeout(relayoutPlotly, 900)
}

window.addEventListener('afterprint', resetLayout)

document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        const printButton = document.querySelector("#print-button")
        printButton.addEventListener("click", resizeForPrinting)
        printButton.disabled = false
    }, 1000)
})
