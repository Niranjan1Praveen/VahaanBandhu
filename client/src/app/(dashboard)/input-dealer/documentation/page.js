"use client";

import React from "react";
import Link from "next/link";
import { BookOpen, Truck, Map, UserPlus, ExternalLink } from "lucide-react";

const docs = [
  {
    title: "शुरुआत कैसे करें",
    description: "नए उपयोगकर्ताओं के लिए प्लेटफ़ॉर्म पर पंजीकरण और लॉगिन प्रक्रिया।",
    href: "/input-dealer/documentation",
    icon: UserPlus,
  },
  {
    title: "वाहन अनुरोध प्रक्रिया",
    description: "किसानों द्वारा ट्रांसपोर्ट अनुरोध करने की पूरी प्रक्रिया को समझें।",
    href: "/input-dealer/documentation",
    icon: Truck,
  },
  {
    title: "रियल-टाइम ट्रैकिंग",
    description: "ट्रक की वर्तमान स्थिति और डिलीवरी स्टेटस को ट्रैक करने के तरीके।",
    href: "/input-dealer/documentation",
    icon: Map,
  },
  {
    title: "साझेदार एकीकरण",
    description: "हमारे साथ जुड़ने के तरीके और अन्य प्लेटफॉर्म के साथ एकीकरण।",
    href: "/input-dealer/documentation",
    icon: BookOpen,
  },
];

function DocumentationPage() {
  return (
    <div className="max-w-4xl p-6">
      <h1 className="text-4xl font-bold mb-6">डॉक्यूमेंटेशन</h1>
      <p className="text-muted-foreground mb-12">
        इस प्लेटफ़ॉर्म का उपयोग कैसे करें, वाहन अनुरोध कैसे भेजें, और ट्रैकिंग फीचर्स को कैसे
        इस्तेमाल करें – इन सभी के लिए मार्गदर्शिका।
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {docs.map(({ title, description, href, icon: Icon, external }) => (
          <Link
            key={title}
            href={href}
            target={external ? "_blank" : "_self"}
            rel={external ? "noopener noreferrer" : undefined}
            className="border border-white/10 p-6 rounded-xl hover:bg-neutral-900 transition-colors duration-300"
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="bg-indigo-600/20 p-2 rounded-lg">
                <Icon className="text-indigo-500 size-6" />
              </div>
              <h2 className="text-xl font-semibold">{title}</h2>
            </div>
            <p className="text-muted-foreground">{description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default DocumentationPage;
