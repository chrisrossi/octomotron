var templates = [];

function compile_templates() {
    $('script[type="text/x-handlebars-template"]').each(
        function(index, element) {
            var element = $(element);
            templates[element.attr('id')] = Handlebars.compile(element.html());
        });
}

function load_sites() {
    $.ajax({
        url: '/OCTOMOTRON/get_sites',
        success: function(data, textStatus, xhr) {
            $('div#sites').html(templates['sites'](data))
        }});
}

$(document).ready(function() {
    compile_templates();
    load_sites();
});
