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
// Establecer un temporizador para ocultar la alerta después de 5 segundos (5000 milisegundos)
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var flashMessages = document.querySelectorAll('.alert');
        flashMessages.forEach(function(message) {
            message.style.display = 'none';
        });
    }, 5000);
});