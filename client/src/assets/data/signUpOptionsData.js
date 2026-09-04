/**
 * Sign-up card data.
 *
 * Text lives in the i18n dictionary and is looked up by `tkey`, so the cards
 * switch language with the rest of the page. Only the non-text attributes
 * (colour, image, layout, destination) live here.
 */
const signUpOptionsData = [
  {
    id: 1,
    tkey: "farmer",
    color: "green",
    img: "/assets/images/farmer.png",
    className: "md:col-span-2 lg:col-span-1",
    to: "/app/farmer",
  },
  {
    id: 2,
    tkey: "trucker",
    color: "lime",
    img: "/assets/images/trucker.png",
    className: "",
    to: "/app/trucker",
    highlight: true,
  },
  {
    id: 3,
    tkey: "dealer",
    color: "green",
    img: "/assets/images/dealer.png",
    className: "",
    to: "/app/dealer",
  },
];

export default signUpOptionsData;
