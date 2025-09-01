setTimeout(function() {
    // Seleciona todos os alertas visíveis
    var alerts = document.querySelectorAll('.alert');
    
    // Itera sobre todos os alertas e os remove após 2 segundos
    alerts.forEach(function(alert) {
        alert.classList.add('fade');
        alert.classList.remove('show');
    });
}, 2000); // 2000ms = 2 segundos