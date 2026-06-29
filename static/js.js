
// FOR ADDING AND REDUCING QUANTITY
document.addEventListener("DOMContentLoaded", () => {

    const addBtn = document.querySelector('#add');
    const minusBtn = document.querySelector('#minus');
    const valueInput = document.querySelector('#value');

    const basePriceEl = document.querySelector('#currentprice');
    const totalPriceEl = document.querySelector('#price');

    const form = document.querySelector('form');
    const quantityField = form.querySelector('input[name="quantity"]');
    const priceField = form.querySelector('input[name="price"]');

    // Extract numeric price (remove ₦)
    const getBasePrice = () => {
        return parseFloat(
            basePriceEl.innerText
                .replace('₦', '')
                .replace(/,/g, '')
                .trim()
        ) || 0;
    };

    // Update total price + hidden inputs
    const updatePrice = () => {
        let quantity = parseInt(valueInput.value) || 1;
        let basePrice = getBasePrice();

        let total = basePrice * quantity;

        // totalPriceEl.innerText = total;
        totalPriceEl.innerText = total.toLocaleString();

        // update hidden inputs
        quantityField.value = quantity;
        priceField.value = total;
    };

    // Add
    addBtn.addEventListener('click', () => {
        valueInput.value = parseInt(valueInput.value) + 1;
        updatePrice();
        console.log("added")
    });

    // Minus (not below 1)
    minusBtn.addEventListener('click', () => {
        let current = parseInt(valueInput.value);

        if (current > 1) {
            valueInput.value = current - 1;
            updatePrice();
        }
    });

    // Manual input change
    valueInput.addEventListener('input', () => {
        if (valueInput.value < 1 || valueInput.value === "") {
            valueInput.value = 1;
        }
        updatePrice();
    });

    // WhatsApp submit
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        const name = document.querySelector('#name').innerText.trim();
        const image = document.querySelector('#food-image').src;

        const quantity = quantityField.value;
        const price = priceField.value;
        const address = document.querySelector('#address').value;

        const message = `
            Hello, I want to order:

            Food: ${name}
            Image: ${image}
            Quantity: ${quantity}
            Total: ₦${price}
            Address: ${address}
        `;

        const phone = document.querySelector('#number').innerText;

        const url = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;

        window.open(url, "_blank");
    });

    // Initial calculation
    updatePrice();
});