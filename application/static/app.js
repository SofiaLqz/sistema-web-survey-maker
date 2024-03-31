// Función que es invocada por la barra de búsqueda para filtrar resultados presentes en el elemento #tabla
function filtrar() {
    var input, filter, table, tr, td, i, j, visible;
    input = document.getElementById("buscar");
    filter = input.value.toUpperCase();
    table = document.getElementById("tabla");
    tr = table.getElementsByTagName("tr");
    if (filter === '') {
        // Si el campo de búsqueda está vacío, muestra todos los elementos
        for (var i = 0; i < tr.length; i++) {
            tr[i].style.display = "";
        }
    } else {
        for (i = 0; i < tr.length; i++) {
            visible = false;
            td = tr[i].getElementsByTagName("td");
            for (j = 0; j < td.length; j++) {
                if (td[j] && td[j].innerHTML.toUpperCase().indexOf(filter) > -1) {
                    visible = true;
                }
            }
            if (visible === true) {
                tr[i].style.display = "";
            } else {
            tr[i].style.display = "none";
            }
        }
    }
}
// Obtener el elemento de la alerta
//var alertElement = document.querySelector('.alert');
// Establecer un temporizador para ocultar la alerta después de 5 segundos (5000 milisegundos)
//setTimeout(function() {
    //alertElement.style.display = 'none';
//}, 5000);
