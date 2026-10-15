let orderList = [];
function order(food, price, quantity) {
    quantity = Number(quantity);
    if (quantity < 1) {
        alert("Please enter a valid quantity.");
        return;
    }
    let existingOrder = orderList.find(order => order.food === food);
    if (existingOrder) {
        existingOrder.quantity += quantity;
        existingOrder.total = existingOrder.price * existingOrder.quantity;
    } else {
        orderList.push({ food, price, quantity, total: price * quantity });
    }
    showOrder();
}
    function showOrder(){
        let orderListElement = document.getElementById("orderList");
        let totalAmountElement = document.getElementById("totalAmount");
        orderListElement.innerHTML = "";
        let totalAmount = 0;
        orderList.forEach(order => {
            let orderTotal = order.price * order.quantity;
            totalAmount += orderTotal;
            let orderItem = document.createElement("p");
            orderItem.textContent = order.food + " x " + order.quantity + " = Ksh " + orderTotal;
            orderListElement.appendChild(orderItem);
        });
        totalAmountElement.textContent = totalAmount;
}
function clearOrder() {
    orderList = [];
    showOrder();
    document.getElementById("orderStatus").textContent = "Pending";
}
function checkout() {
    if (orderList.length === 0) {
        alert("Your order is empty. Please add items to your order before checking out.");
        return;
    }
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/checkout";

    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "cart_data";
    input.value = JSON.stringify(orderList);

    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
}
function confirmOrder() {
    if (orderList.length === 0) {
        alert("Your order is empty. Please add items to your order before confirming.");
        return;
    }
    document.getElementById("orderStatus").textContent = "Order placed-Pending";
    document.getElementById("orderStatus").textContent = "Confirmed";
    alert("Your order has been confirmed!");
}