import FeatureCard from "@/components/ui/featureCard";
import Tags from "@/components/ui/tags";
import Image from "next/image";
import Key from "@/components/ui/key";
import featureMap from "@/assets/images/feature-map.png";
const features = [
  "खाली लौटने से बचाव",
  "एफपीओ और यूनियन इंटीग्रेशन",
  "कम नेटवर्क में भी काम करता है",
  "स्थानीय भाषा में समर्थन",
  "बाजार मूल्य अलर्ट",
  "सीधा किसान-ड्राइवर समन्वय",
  "डिजिटल भुगतान सुविधा",
  "ESG व CSR ट्रैकिंग",
];

export default function Features() {
  return (
    <section
      className="py-24 px-4 flex items-center justify-center"
      id="features"
    >
      <div className="container">
        <div className="flex justify-center">
          <Tags title={"प्लेटफ़ॉर्म विशेषताएँ"} />
        </div>
        <h2 className="text-6xl font-medium text-center mt-6 max-w-3xl mx-auto">
          <span className="text-lime-400">सामाजिक प्रभाव</span> के लिए तकनीक
        </h2>

        {/* Feature Cards */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-4 lg:grid-cols-3 gap-8">
          {/* Card-1 */}
          <FeatureCard
            title={"रीयल-टाइम ट्रैकिंग डैशबोर्ड"}
            description={
              "किसान और ट्रक चालक अपनी बुकिंग, लोकेशन और डिलीवरी स्टेटस को एक ही प्लेटफ़ॉर्म पर लाइव देख सकते हैं — पारदर्शिता और विश्वसनीयता सुनिश्चित करने के लिए।"
            }
            className="md:col-span-2 lg:col-span-1"
          >
            <div className="aspect-video flex items-center justify-center">
              <Image
                alt="feature-map-design"
                src={featureMap}
                className="rounded-xl"
                height={650}
                width={650}
              />
            </div>
          </FeatureCard>

          {/* Card-2 */}
          <FeatureCard
            title={"वॉयस-आधारित ट्रक बुकिंग"}
            description={
              "ग्रामिण इलाकों में कम डिजिटल साक्षरता को ध्यान में रखते हुए, किसान अपनी स्थानीय भाषा में सिर्फ़ कॉल करके ट्रक बुक कर सकते हैं।"
            }
            className="md:col-span-2 lg:col-span-1"
          >
            <div className="aspect-video flex items-center justify-center">
              <p className="text-3xl font-bold text-white/20 text-center leading-relaxed">
                तकनीक जो <br />
                <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text">
                  सुलभ
                </span>{" "}
                हो
              </p>
            </div>
          </FeatureCard>

          {/* Card-3 */}
          <FeatureCard
            title={"AI आधारित रूट ऑप्टिमाइज़ेशन"}
            description={
              "हमारा एल्गोरिद्म ऐसे रूट चुनता है जिससे ट्रक खाली वापस ना लौटें — डीज़ल की बचत और समय की भी। किसान को समय पर डिलीवरी और ट्रक चालक को अतिरिक्त आय।"
            }
            className="md:col-span-2 md:col-start-2 lg:col-span-1 lg:col-start-auto"
          >
            <div className="aspect-video flex items-center justify-center gap-4 flex-wrap">
              <Key className={"w-28"}>कम दूरी</Key>
              <Key className={"w-28"}>कम लागत</Key>
              <Key className={"w-28"}>ज़्यादा लाभ</Key>
            </div>
          </FeatureCard>
        </div>

        {/* Other Features */}
        <div className="mt-8 flex flex-wrap gap-3 justify-center">
          {features.map((feature) => (
            <div
              key={feature}
              className="bg-neutral-900 border-white/10 inline-flex gap-3 items-center px-3 md:px-5 py-1.5 md:py-2 rounded-2xl hover:scale-105 transition duration-500 group"
            >
              <span className="bg-lime-400 text-neutral-950 size-5 rounded-full inline-flex items-center justify-center text-xl group-hover:rotate-45 transition duration-500">
                &#10038;
              </span>
              <span className="font-medium md:text-lg">{feature}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
