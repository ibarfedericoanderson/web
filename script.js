document.addEventListener('DOMContentLoaded', function() {
    // Manejar la generación de QRGB
    document.getElementById('qrgb-form').addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(this);

        fetch('/generate_qrgb', {
            method: 'POST',
            body: formData
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'superposed_qr.png';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });

    // Manejar la decodificación de QRGB
    document.getElementById('decode-form').addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(this);

        fetch('/decode_qr', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = `
                <h3>Resultados de Decodificación:</h3>
                <p>Capa Roja: ${data.red || 'No decodificado'}</p>
                <p>Capa Verde: ${data.green || 'No decodificado'}</p>
                <p>Capa Azul: ${data.blue || 'No decodificado'}</p>
            `;
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
