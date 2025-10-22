function toggleSection(button) {
    const list = button.nextElementSibling;
    const icon = button.querySelector(".icon");
    if (list.style.display === "block") {
        list.style.display = "none";
        icon.textContent = "+";
    } else {
        list.style.display = "block";
        icon.textContent = "-";
    }
}
