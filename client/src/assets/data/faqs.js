export const faqs = [
  {
    question: "What is the purpose of this platform?",
    answer:
      "Our platform enables farmers to book affordable truck transport using voice commands in their local language, reducing delays, spoilage, and high logistics costs.",
  },
  {
    question: "Who can use this platform?",
    answer:
      "The platform is built for smallholder farmers, FPOs (Farmer Producer Organizations), transporters, and buyers looking to streamline last-mile agricultural logistics.",
  },
  {
    question: "How do farmers book a truck?",
    answer:
      "Farmers simply speak their request using our voice-driven interface. The system understands the request, finds nearby trucks, and confirms the booking—no typing required.",
  },
  {
    question: "How does the voice system work?",
    answer:
      "We use the Gemini API to understand local-language voice inputs. These are converted into structured requests, matched with drivers, and routed through an optimized algorithm.",
  },
  {
    question: "How are drivers matched and routes optimized?",
    answer:
      "Our backend uses decision-tree logic and Vertex AI models to match drivers in real time and determine the shortest, most cost-effective delivery routes.",
  },
  {
    question: "Can the platform work in low network areas?",
    answer:
      "Yes, the app is optimized for rural, low-connectivity areas with offline-first features and fallback SMS/WhatsApp confirmations when possible.",
  },
  {
    question: "Is the service secure?",
    answer:
      "Yes, we use JWT authentication, AES encryption, and TLS protocols to ensure all user and logistics data is securely stored and transmitted.",
  },
  {
    question: "What features are coming soon?",
    answer:
      "Future updates include support for more regional languages, integration with government mandi APIs, and sustainability insights for route planning.",
  },
];
