/**
 * Lightweight i18n.
 *
 * VahaanBandhu is Hindi-first, so `hi` is the default and every key must have a
 * Hindi value. English exists so the interface is maintainable and testable, not
 * because it is the primary surface.
 *
 * Deliberately a plain dictionary rather than a full i18n framework: the string
 * count is small, and scattering hundreds of hardcoded strings through
 * components was the actual problem to avoid.
 */

export const LANGUAGES = ["hi", "en"];
export const DEFAULT_LANGUAGE = "hi";

const dict = {
  hi: {
    "app.name": "वाहनबन्धु",
    "app.tagline": "गाँव से मंडी तक, और वापसी में भी कमाई",

    "nav.dashboard": "डैशबोर्ड",
    "nav.requests": "अनुरोध",
    "nav.jobs": "काम",
    "nav.requirements": "ज़रूरतें",
    "nav.newRequest": "नया अनुरोध",
    "nav.signIn": "लॉग इन",
    "nav.signUp": "शुरू करें",
    "nav.signOut": "लॉग आउट",

    "role.question": "मैं कौन हूँ?",
    "role.subtitle": "अपनी भूमिका चुनें ताकि हम आपको सही जानकारी दिखा सकें",
    "role.farmer": "किसान",
    "role.farmer.desc": "फसल मंडी तक पहुँचानी है",
    "role.trucker": "ट्रक चालक",
    "role.trucker.desc": "गाड़ी है, काम चाहिए",
    "role.dealer": "इनपुट डीलर",
    "role.dealer.desc": "दुकान के लिए सामान मंगवाना है",
    "role.continue": "आगे बढ़ें",

    "farmer.title": "किसान डैशबोर्ड",
    "farmer.newRequest": "नया परिवहन अनुरोध",
    "farmer.crop": "फसल",
    "farmer.mandi": "मंडी",
    "farmer.quantity": "मात्रा",
    "farmer.unit": "इकाई",
    "farmer.origin": "गाँव / उठान स्थान",
    "farmer.submit": "अनुरोध भेजें",
    "farmer.myRequests": "मेरे अनुरोध",
    "farmer.noRequests": "अभी कोई अनुरोध नहीं है",
    "farmer.noRequests.hint": "ऊपर से नया अनुरोध बनाएं",
    "farmer.clarify": "जानकारी चाहिए",
    "farmer.bagWeight": "एक बोरी में कितने किलो?",
    "farmer.confirm": "पुष्टि करें",
    "farmer.viewRoute": "रास्ता देखें",

    "trucker.title": "ट्रक चालक डैशबोर्ड",
    "trucker.available": "उपलब्ध",
    "trucker.unavailable": "अनुपलब्ध",
    "trucker.myVehicle": "मेरी गाड़ी",
    "trucker.capacity": "क्षमता",
    "trucker.openJobs": "उपलब्ध काम",
    "trucker.myJobs": "मेरे काम",
    "trucker.noJobs": "अभी कोई काम उपलब्ध नहीं है",
    "trucker.accept": "काम स्वीकारें",
    "trucker.returnLoads": "वापसी लोड",
    "trucker.returnLoads.desc": "मंडी से लौटते समय यह सामान ले जाएँ",
    "trucker.noReturnLoads": "इस समय कोई वापसी लोड नहीं मिला",
    "trucker.emptyKmAvoided": "खाली किलोमीटर बचे",
    "trucker.detour": "अतिरिक्त दूरी",
    "trucker.earning": "अनुमानित कमाई",

    "dealer.title": "इनपुट डीलर डैशबोर्ड",
    "dealer.newRequirement": "नई ज़रूरत",
    "dealer.material": "सामग्री",
    "dealer.quantity": "मात्रा",
    "dealer.deliveryLocation": "डिलीवरी स्थान",
    "dealer.neededBy": "कब तक चाहिए",
    "dealer.submit": "ज़रूरत दर्ज करें",
    "dealer.myRequirements": "मेरी ज़रूरतें",
    "dealer.incoming": "आने वाला सामान",
    "dealer.noRequirements": "अभी कोई ज़रूरत दर्ज नहीं है",
    "dealer.matchedTruck": "मिली गाड़ी",

    "route.title": "रास्ता",
    "route.distance": "दूरी",
    "route.eta": "अनुमानित समय",
    "route.cost": "अनुमानित खर्च",
    "route.emptyKm": "खाली किलोमीटर",
    "route.why": "यह रास्ता क्यों?",
    "route.engine": "VB-QER द्वारा अनुकूलित",

    "status.DRAFT": "अधूरा",
    "status.REQUESTED": "अनुरोध भेजा",
    "status.MATCHING": "गाड़ी खोजी जा रही है",
    "status.MATCHED": "गाड़ी मिली",
    "status.ACCEPTED": "स्वीकृत",
    "status.PICKUP": "उठान",
    "status.IN_TRANSIT": "रास्ते में",
    "status.AT_MANDI": "मंडी पहुँचा",
    "status.RETURN_LOAD": "वापसी लोड",
    "status.COMPLETED": "पूरा हुआ",
    "status.CANCELLED": "रद्द",
    "status.OPEN": "खुला",
    "status.DELIVERED": "पहुँचा दिया",

    "unit.kg": "किलो",
    "unit.bori": "बोरी",
    "unit.quintal": "क्विंटल",
    "unit.tonne": "टन",

    "common.loading": "लोड हो रहा है…",
    "common.error": "कुछ गड़बड़ हुई",
    "common.retry": "फिर कोशिश करें",
    "common.cancel": "रद्द करें",
    "common.save": "सहेजें",
    "common.km": "कि.मी.",
    "common.min": "मिनट",
    "common.backendDown": "सर्वर उपलब्ध नहीं है। कृपया थोड़ी देर बाद कोशिश करें।",
    "common.demoMode": "डेमो मोड",
  },

  en: {
    "app.name": "VahaanBandhu",
    "app.tagline": "Village to mandi — and earning on the way back",

    "nav.dashboard": "Dashboard",
    "nav.requests": "Requests",
    "nav.jobs": "Jobs",
    "nav.requirements": "Requirements",
    "nav.newRequest": "New request",
    "nav.signIn": "Sign in",
    "nav.signUp": "Get started",
    "nav.signOut": "Sign out",

    "role.question": "Who am I?",
    "role.subtitle": "Pick your role so we can show you the right things",
    "role.farmer": "Farmer",
    "role.farmer.desc": "I need crops moved to a mandi",
    "role.trucker": "Truck driver",
    "role.trucker.desc": "I have a vehicle and want work",
    "role.dealer": "Input dealer",
    "role.dealer.desc": "I need stock delivered to my shop",
    "role.continue": "Continue",

    "farmer.title": "Farmer dashboard",
    "farmer.newRequest": "New transport request",
    "farmer.crop": "Crop",
    "farmer.mandi": "Mandi",
    "farmer.quantity": "Quantity",
    "farmer.unit": "Unit",
    "farmer.origin": "Village / pickup point",
    "farmer.submit": "Send request",
    "farmer.myRequests": "My requests",
    "farmer.noRequests": "No requests yet",
    "farmer.noRequests.hint": "Create one above",
    "farmer.clarify": "Needs clarification",
    "farmer.bagWeight": "How many kg in one bori?",
    "farmer.confirm": "Confirm",
    "farmer.viewRoute": "View route",

    "trucker.title": "Trucker dashboard",
    "trucker.available": "Available",
    "trucker.unavailable": "Unavailable",
    "trucker.myVehicle": "My vehicle",
    "trucker.capacity": "Capacity",
    "trucker.openJobs": "Open jobs",
    "trucker.myJobs": "My jobs",
    "trucker.noJobs": "No jobs available right now",
    "trucker.accept": "Accept job",
    "trucker.returnLoads": "Return loads",
    "trucker.returnLoads.desc": "Carry these on the way back from the mandi",
    "trucker.noReturnLoads": "No return loads found right now",
    "trucker.emptyKmAvoided": "Empty km avoided",
    "trucker.detour": "Extra distance",
    "trucker.earning": "Estimated earning",

    "dealer.title": "Input dealer dashboard",
    "dealer.newRequirement": "New requirement",
    "dealer.material": "Material",
    "dealer.quantity": "Quantity",
    "dealer.deliveryLocation": "Delivery location",
    "dealer.neededBy": "Needed by",
    "dealer.submit": "Create requirement",
    "dealer.myRequirements": "My requirements",
    "dealer.incoming": "Incoming deliveries",
    "dealer.noRequirements": "No requirements yet",
    "dealer.matchedTruck": "Matched vehicle",

    "route.title": "Route",
    "route.distance": "Distance",
    "route.eta": "Estimated time",
    "route.cost": "Estimated cost",
    "route.emptyKm": "Empty km",
    "route.why": "Why this route?",
    "route.engine": "Optimized by VB-QER",

    "status.DRAFT": "Draft",
    "status.REQUESTED": "Requested",
    "status.MATCHING": "Finding a vehicle",
    "status.MATCHED": "Vehicle found",
    "status.ACCEPTED": "Accepted",
    "status.PICKUP": "Pickup",
    "status.IN_TRANSIT": "In transit",
    "status.AT_MANDI": "At mandi",
    "status.RETURN_LOAD": "Return load",
    "status.COMPLETED": "Completed",
    "status.CANCELLED": "Cancelled",
    "status.OPEN": "Open",
    "status.DELIVERED": "Delivered",

    "unit.kg": "kg",
    "unit.bori": "bori",
    "unit.quintal": "quintal",
    "unit.tonne": "tonne",

    "common.loading": "Loading…",
    "common.error": "Something went wrong",
    "common.retry": "Try again",
    "common.cancel": "Cancel",
    "common.save": "Save",
    "common.km": "km",
    "common.min": "min",
    "common.backendDown": "The server is unavailable. Please try again shortly.",
    "common.demoMode": "Demo mode",
  },
};

/** Translate. Falls back to Hindi, then to the key itself — never blank. */
export function t(key, lang = DEFAULT_LANGUAGE) {
  return dict[lang]?.[key] ?? dict[DEFAULT_LANGUAGE]?.[key] ?? key;
}

export function useT(lang = DEFAULT_LANGUAGE) {
  return (key) => t(key, lang);
}

export default dict;
