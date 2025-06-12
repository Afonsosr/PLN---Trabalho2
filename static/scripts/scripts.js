
// Função para fazer a tabela 
$(document).ready( function () {
    $('#myTable').DataTable();
} );

// No método de pesquisa esta função oculete aquelas letras que não têm palavras 
$(document).ready(function(){
    $("#myInput").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $(".list-group-item").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });

        $(".letra-section").each(function() {
            var section = $(this);
            var hasVisibleItems = section.find(".list-group-item:visible").length > 0;
            section.toggle(hasVisibleItems);
        });
    });
});

