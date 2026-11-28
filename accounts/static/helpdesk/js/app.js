const menuToggle = document.querySelector(".menu-toggle");
const accountMenu = document.getElementById("account-menu");

if (menuToggle && accountMenu) {
  const mobile = window.matchMedia("(max-width: 48rem)");

  function updateMenu(expanded) {
    accountMenu.hidden = !expanded;
    menuToggle.setAttribute("aria-expanded", String(expanded));
  }

  function applyLayout() {
    menuToggle.hidden = !mobile.matches;
    updateMenu(!mobile.matches);
  }

  menuToggle.addEventListener("click", () => updateMenu(accountMenu.hidden));

  accountMenu.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && mobile.matches) {
      updateMenu(false);
      menuToggle.focus();
    }
  });

  mobile.addEventListener("change", applyLayout);
  applyLayout();
}

document.addEventListener("click", (event) => {
  const trigger = event.target.closest("button[data-open-dialog]");
  if (!trigger) return;

  const dialog = document.getElementById(trigger.dataset.openDialog);
  if (dialog instanceof HTMLDialogElement && !dialog.open) {
    dialog.showModal();
  }
});
