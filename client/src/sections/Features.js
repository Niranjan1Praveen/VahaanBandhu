"use client";
import { t } from "@/lib/i18n";
import { useSession } from "@/components/providers/SessionProvider";
import FeatureCard from "@/components/ui/featureCard";
import Tags from "@/components/ui/tags";
import Image from "next/image";
import Key from "@/components/ui/key";
import featureMap from "@/assets/images/feature-map.png";
// Pill labels come from the dictionary; see features.pills.

export default function Features() {
  const { lang } = useSession();
  const tr = (k) => t(k, lang);
  return (
    <section
      className="py-24 px-4 flex items-center justify-center"
      id="features"
    >
      <div className="container">
        <div className="flex justify-center">
          <Tags title={tr("features.tag")} />
        </div>
        <h2 className="text-6xl font-medium text-center mt-6 max-w-3xl mx-auto">
          {lang === "hi" ? (<>
            <span className="text-lime-400">{tr("features.title.accent")}</span>{" "}
            {tr("features.title.rest")}
          </>) : (<>
            {tr("features.title.rest")}{" "}
            <span className="text-lime-400">{tr("features.title.accent")}</span>
          </>)}
        </h2>

        {/* Feature Cards */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-4 lg:grid-cols-3 gap-8">
          {/* Card-1 */}
          <FeatureCard
            title={tr("features.tracking.title")}
            description={
              tr("features.tracking.desc")
            }
            className="md:col-span-2 lg:col-span-1"
          >
            <div className="aspect-video flex items-center justify-center">
              <Image
                alt="feature-map-design"
                src={featureMap}
                className="rounded-xl"
                height={450}
                width={450}
              />
            </div>
          </FeatureCard>

          {/* Card-2 */}
          <FeatureCard
            title={tr("features.voice.title")}
            description={
              tr("features.voice.desc")
            }
            className="md:col-span-2 lg:col-span-1"
          >
            <div className="aspect-video flex items-center justify-center">
              <p className="text-3xl font-bold text-white/20 text-center leading-relaxed">
                {tr("features.accessible.pre")} <br />
                <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text">
                  {tr("features.accessible.accent")}
                </span>{" "}
                {tr("features.accessible.post")}
              </p>
            </div>
          </FeatureCard>

          {/* Card-3 */}
          <FeatureCard
            title={tr("features.route.title")}
            description={
              tr("features.route.desc")
            }
            className="md:col-span-2 md:col-start-2 lg:col-span-1 lg:col-start-auto"
          >
            <div className="aspect-video flex items-center justify-center gap-4 flex-wrap">
              <Key className={"w-28"}>{tr("features.key.shortdist")}</Key>
              <Key className={"w-28"}>{tr("features.key.lowcost")}</Key>
              <Key className={"w-28"}>{tr("features.key.moreprofit")}</Key>
            </div>
          </FeatureCard>
        </div>

        {/* Other Features */}
        <div className="mt-8 flex flex-wrap gap-3 justify-center">
          {tr('features.pills').map((feature) => (
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
