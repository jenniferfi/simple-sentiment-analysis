function displaySelectedFileName() {
  const fileInput = document.querySelector('#file-upload input[type=file]');

  if (fileInput != null) {
    fileInput.onchange = () => {
      if (fileInput.files.length > 0) {
        const fileName = document.querySelector('#file-upload .file-name');
        fileName.textContent = fileInput.files[0].name;
      }
    }
  }
}

window.addEventListener('pageshow', () => {
  displaySelectedFileName();
});

// TODO: Need all these?
function turnButtonToLoadingIcon(btnId) {
  let button = document.querySelector(`#${btnId}`);
  button.classList.add('is-loading');
}

function disableButton(btnIds) {
  btnIds.forEach((element)=>
      document.querySelector(`#${element}`).setAttribute('disabled', '')
  );
}

function showElement(id){
    let element = document.getElementById(id);
    element.classList.remove('hidden');
}

function hideElement(id) {
    let element = document.getElementById(id);
    element.classList.add('hidden');
}

// Modals
document.addEventListener('DOMContentLoaded', () => {
  // Functions to open and close a modal
  function openModal($el) {
    $el.classList.add('is-active');
  }

  function closeModal($el) {
    $el.classList.remove('is-active');
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

  // Add a click event on buttons to open a specific modal
  (document.querySelectorAll('.open-info-modal') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);

    $trigger.addEventListener('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  // Add a keyboard event to close all modals
  document.addEventListener('keydown', (event) => {
    const e = event || window.event;

    if (e.keyCode === 27) { // Escape key
      closeAllModals();
    }
  });
});