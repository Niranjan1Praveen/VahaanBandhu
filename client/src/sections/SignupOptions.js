"use client";
import { t } from "@/lib/i18n";
import { useSession } from "@/components/providers/SessionProvider";
import signUpOptionsData from "../assets/data/signUpOptionsData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { motion } from "framer-motion";
import Tags from "@/components/ui/tags";
import Link from "next/link";

const SignUpOptions = () => {
  const { lang } = useSession();
  const tr = (k) => t(k, lang);
  return (
    <section
      className="py-24 px-4 flex items-center justify-center"
      id="signUpOptions"
    >
      <div className="container">
        <div className="flex justify-center">
          <Tags title={tr("signup.tag")} />
        </div>
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 items-center lg:items-end mx-auto">
          {signUpOptionsData.map((plan, idx) => (
            <Card
              key={idx}
              className={cn(
                "flex flex-col justify-between shadow-md transition-all duration-300 bg-transparent border-0"
              )}
            >
              <CardContent className="p-10 space-y-6 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-semibold">{tr(`signup.${plan.tkey}.title`)}</h3>

                    {plan.popular && (
                      <div className="inline-flex text-sm px-4 py-1.5 rounded-xl border border-white/20">
                        <motion.span
                          animate={{
                            backgroundPositionX: "-100%",
                          }}
                          transition={{
                            duration: 1,
                            repeat: Infinity,
                            ease: "linear",
                            repeatType: "loop",
                          }}
                          className="bg-[linear-gradient(to_right,#DD7DDF,#E1CD86,#BBCB92,#71C2EF,#3BFFFF,#DD7DDF)] [background-size:200%] text-transparent bg-clip-text font-medium"
                        >
                          {tr("signup.driverChoice")}
                        </motion.span>
                      </div>
                    )}
                  </div>
                  <div className="mt-6 space-y-4">
                    <p className="font-medium leading-normal text-muted-foreground">
                      {tr(`signup.${plan.tkey}.desc`)}
                    </p>
                    {plan.id === 1 && (
                      <Link href={"/app/farmer"}>
                        <Button className="cursor-pointer w-full">{tr("signup.book")}</Button>
                      </Link>
                    )}
                    {plan.id === 2 && (
                      <Link href={"/app/trucker"}>
                        <Button className="cursor-pointer w-full">{tr("signup.pickup")}</Button>
                      </Link>
                    )}
                    {plan.id === 3 && (
                      <Link href="/signin">
                        <Button className="cursor-pointer w-full">{tr("signup.register")}</Button>
                      </Link>
                    )}
                  </div>
                  <ul className="mt-6 space-y-2 text-sm">
                    {(tr(`signup.${plan.tkey}.features`) || []).map((feature, i) => (
                      <li key={i} className="flex items-start">
                        <Check className="text-lime-400 mr-2" /> {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default SignUpOptions;
