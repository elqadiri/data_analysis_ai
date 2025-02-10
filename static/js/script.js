// Sélectionnez les éléments nécessaires
const uploadModal = document.getElementById('uploadModal');
const uploadFormModal = document.getElementById('uploadFormModal');
const uploadResponseModal = document.getElementById('uploadResponseModal');

// Afficher la modale au chargement de la page
window.onload = function () {
    uploadModal.classList.remove('hidden');
};

    // Fonction pour uploader le dataset
async function uploadDatasetModal() {
const fileInput = document.getElementById('datasetFileModal');
const uploadResponse = document.getElementById('uploadResponseModal');

if (fileInput.files.length === 0) {
    uploadResponse.textContent = 'Aucun fichier sélectionné.';
    uploadResponse.classList.remove('hidden');
    return;
}

const formData = new FormData();
formData.append('datasetFile', fileInput.files[0]);

try {
    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    const data = await response.json();
    
    uploadResponseModal.textContent = response.ok 
        ? data.message 
        : (data.error || 'Erreur lors de l\'upload.');
    uploadResponseModal.classList.remove('hidden');

    if (response.ok) {
        // Masquer le modal après un upload réussi
        uploadModal.classList.add('hidden');
    }
} catch (error) {
    console.error(error);
    uploadResponseModal.textContent = 'Erreur lors de l\'upload.';
    uploadResponseModal.classList.remove('hidden');
}
}
document.getElementById('datasetFileModal').addEventListener('change', function() {
    const fileName = this.files[0] ? this.files[0].name : 'Aucun fichier choisi';
    console.log('Fichier sélectionné :', fileName);
});

function appendMessage(role, text) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageElement = document.createElement('div');
    messageElement.className = 'p-3 rounded';

    if (role === 'user') {
        messageElement.classList.add('bg-blue-100', 'text-blue-900');
        messageElement.textContent = "Vous: " + text;
    } else if (role === 'assistant') {
        messageElement.classList.add('bg-green-100', 'text-green-900');
        messageElement.textContent = "Assistant: " + text;
    } else {
        // Pour les erreurs ou autres
        messageElement.classList.add('bg-red-100', 'text-red-900');
        messageElement.textContent = "Erreur: " + text;
    }

    chatMessages.appendChild(messageElement);
    // Scroller en bas pour voir le dernier message
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fonction pour exécuter le code
function executeCode() {
    // Récupérer le code modifié depuis le textarea
    const editableCode = document.getElementById('editableCode').value;

    // Envoyer le code modifié au backend pour exécution
    fetch('/api/execute_code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: editableCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.result) {
            // Afficher le résultat de l'exécution
            document.getElementById('executionResult').innerHTML = data.result;
        } else {
            alert('Erreur : ' + data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

// Fonction pour envoyer une question à Llama et afficher le code généré
function sendPrompt() {
    const userPrompt = document.getElementById('userPrompt').value;

    // Envoyer la question au backend
    fetch('/api/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            // Afficher le code généré dans le textarea éditable
            document.getElementById('editableCode').value = data.response;
            // Afficher la section "Exécuter le Code"
            document.getElementById('executeCodeSection').classList.remove('hidden');
        } else {
            alert('Erreur : ' + data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

document.getElementById("download-btn").addEventListener("click", function () {
    fetch("/api/download_dataset", { method: "GET" })
        .then(response => {
            if (!response.ok) {
                alert("Erreur lors du téléchargement du fichier.");
                return;
            }
            return response.blob();
        })
        .then(blob => {
            if (blob) {
                // Créer un lien temporaire pour déclencher le téléchargement
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.download = "modified_dataset.csv";
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            }
        })
        .catch(error => {
            console.error("Erreur :", error);
            alert("Une erreur est survenue lors du téléchargement.");
        });
});

document.addEventListener("DOMContentLoaded", function () {
    const button = document.querySelector(".button-main");
    const icon = button.querySelector(".button-icon");
  
    button.addEventListener("mouseover", function () {
      icon.classList.add("button-icon-hover");
      icon.classList.remove("button-icon-default");
    });
  
    button.addEventListener("mouseleave", function () {
      icon.classList.add("button-icon-default");
      icon.classList.remove("button-icon-hover");
    });
  });
  
// message section
async function loadMessages() {
    const response = await fetch('/get_messages');
    const messages = await response.json();

    const chatContainer = document.getElementById('chatContainer');
    chatContainer.innerHTML = ''; // Efface les messages existants

    // Parcourir les messages et les afficher
    messages.forEach(msg => {
        addMessageToUI(msg.sender, msg.message);
    });
}

// Fonction pour ajouter un message à l'interface utilisateur
function addMessageToUI(sender, message, isQuestion = false) {
    const chatContainer = document.getElementById('chatContainer');
    
    // Créer un conteneur pour le message
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'chat-message-user' : 'chat-message-system';
    messageDiv.textContent = message;
    
    if (isQuestion) {
        // Insérer la question en haut
        chatContainer.prepend(messageDiv);
    } else {
        // Ajouter la réponse juste après la question
        chatContainer.insertBefore(messageDiv, chatContainer.firstChild.nextSibling);
    }
    
    // Faire défiler vers le haut (optionnel)
    chatContainer.scrollTop = 0;
}

// Gestion de l'envoi de message
function sendPrompt2() {
    const userPrompt = document.getElementById('userPrompt').value.trim();

    // Vérifie si le champ est vide
    if (userPrompt === "") {
        alert("Veuillez entrer un message.");
        return;
    }

    // 1. Sauvegarder le message dans la base de données
    fetch('/save_message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userPrompt })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || "Erreur lors de l'enregistrement du message.");
        }
        return data;
    })
    .then(() => {
        // 2. Ajouter la question à l'interface utilisateur
        addMessageToUI('user', userPrompt, true);
        document.getElementById('userPrompt').value = "";
    })
    .then(() => {
        // 3. Envoyer la question au backend pour traitement
        return fetch('/api/prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: userPrompt })
        });
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            const generatedCode = data.response;
            document.getElementById('editableCode').value = generatedCode;
            document.getElementById('executeCodeSection').classList.remove('hidden');
            
            // Ajouter la réponse juste après la question
            addMessageToUI('system', `Résultat : ${generatedCode}`);
        } else {
            throw new Error(data.error || "Erreur lors du traitement de la requête.");
        }
    })
    .catch(error => {
        console.error("Erreur :", error);
        alert("Une erreur s'est produite : " + error.message);
    });
}
window.onload = loadMessages;
