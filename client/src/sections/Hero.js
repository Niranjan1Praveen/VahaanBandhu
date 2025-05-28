"use client";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import heroDesign from "@/assets/images/hero.png";
import { Truck } from "lucide-react";
import { motion } from "framer-motion";
export default function Hero() {
  return (
    <section className="py-24 px-4 overflow-x-clip">
      <div className="container mx-auto flex flex-col-reverse md:flex-row items-center gap-12">
        <div className="w-full md:w-3/4">
          <div className="flex justify-center md:justify-start">
            <div className="inline-flex py-1 px-3 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full text-neutral-950 font-semibold">
              1,000+ किसानों और ट्रक चालकों को जोड़ते हुए
            </div>
          </div>

          <h1 className="text-4xl md:text-6xl font-medium mt-6 leading-relaxed">
            लॉजिस्टिक्स सुविधा के साथ ग्रामीण परिवहन में क्रांति लाएं
            <div className="relative w-[200px] h-[100px] overflow-hidden inline-flex mx-8">
              <Truck
                size={50}
                className="absolute top-[35px] left-1/2 -translate-x-1/2"
              />
              <motion.div
                className="absolute bottom-0 left-0 h-[20px] w-[200%]"
                style={{
                  background:
                    "repeating-linear-gradient(90deg, black, black 10px, white 10px, white 50px)",
                }}
                animate={{ x: ["0%", "-50%"] }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "linear",
                }}
              />
            </div>
          </h1>

          <p className="text-lg md:text-xl text-white/50 mt-8 leading-relaxed">
            हर खाली लौटते ट्रक को एक अवसर में बदलें। हमारा प्लेटफ़ॉर्म ट्रक
            चालकों और किसानों को जोड़ता है ताकि कृषि उत्पाद समय पर, कम लागत में
            बाज़ार तक पहुँचें। वॉयस बुकिंग, AI-आधारित रूट ऑप्टिमाइज़ेशन, और सटीक
            डिलीवरी ट्रैकिंग से, हम ला रहे हैं ट्रांसपोर्ट में एक नई क्रांति।
          </p>

          <div className="mt-8 flex justify-center md:justify-between">
            <Button
              variant="signup"
              size="sm"
              className="whitespace-nowrap rounded-full"
            >
              <a href="#signUpOptions">शुरू करें</a>
            </Button>
          </div>
        </div>

        <div className="w-full md:w-1/2 flex justify-center md:justify-end">
          <Image
            src={heroDesign}
            alt="Hero"
            width={400}
            height={400}
            priority
          />
        </div>
      </div>
    </section>
  );
}
