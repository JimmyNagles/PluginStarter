window.init = function (container, updateConfig) {
    const wrapper = document.createElement("div");
    wrapper.style.padding = "8px";

    const label = document.createElement("label");
    label.innerText = "Search query:";
    label.style.display = "block";
    label.style.marginBottom = "4px";

    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "e.g. cats, dogs, airplanes";
    input.style.width = "100%";

    input.oninput = () => {
        updateConfig({
            query: input.value
        });
    };

    wrapper.appendChild(label);
    wrapper.appendChild(input);
    container.appendChild(wrapper);

    // Initialize config so task creation is unblocked
    updateConfig({ query: "" });
};
