export const formatCurrency = (amount) => {
  return new Intl.NumberFormat("en-EU", {
    style: "currency",
    currency: "EU",
  }).format(amount);
};
