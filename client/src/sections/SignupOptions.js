"use client";
import signUpOptionsData from "../assets/data/signUpOptionsData";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { motion } from "framer-motion";
import Tags from "@/components/ui/tags";
import { RegisterLink } from "@kinde-oss/kinde-auth-nextjs";
import Link from "next/link";

const SignUpOptions = () => {
  return (
    <section
      className="py-24 px-4 flex items-center justify-center"
      id="signUpOptions"
    >
      <div className="container">
        <div className="flex justify-center">
          <Tags title={"साइन अप विकल्प"} />
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
                    <h3 className="text-xl font-semibold">{plan.title}</h3>

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
                          ड्राइवरों की पहली पसंद
                        </motion.span>
                      </div>
                    )}
                  </div>
                  <div className="mt-6 space-y-4">
                    <p className="font-medium leading-normal text-muted-foreground">
                      {plan.description}
                    </p>
                    {plan.id === 1 && (
                      <Link href={"/farmer/vehicle-request "}>
                        <Button className="cursor-pointer w-full">बुक करें</Button>
                      </Link>
                    )}
                    {plan.id === 2 && (
                      <Link href={"http://127.0.0.1:5000/"}>
                        <Button className="cursor-pointer w-full">उठान शुरू</Button>
                      </Link>
                    )}
                    {plan.id === 3 && (
                      <RegisterLink>
                        <Button className="cursor-pointer w-full">रजिस्टर करें</Button>
                      </RegisterLink>
                    )}
                  </div>
                  <ul className="mt-6 space-y-2 text-sm">
                    {plan.features.map((feature, i) => (
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
