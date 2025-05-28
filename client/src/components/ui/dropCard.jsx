"use client";
import React from "react";
import { twMerge } from "tailwind-merge";
import { Button } from "./button";
import { RegisterLink } from "@kinde-oss/kinde-auth-nextjs/components";
import { Card } from "./card";
import Link from "next/link";

const DropCard = ({ item }) => {
  return (
    <Card
      className={twMerge(
        `
    relative min-h-[350px] overflow-hidden
    transition-all duration-500 ease-in-out rounded-md 
  `,
        item.className
      )}
    >
      <div className="flex flex-col text-white p-4 h-full">
        {/* Content wrapper */}
        <div className="flex flex-col flex-grow space-y-4">
          <h2 className="text-lime-400 text-3xl font-bold">{item.cta}</h2>
          <p className="font-medium text-xl px-2 leading-normal">
            {item.description}
          </p>

          <ul className="text-md text-white/80 mt-4 space-y-2">
            {item.features?.map((point, i) => (
              <li key={i} className="flex gap-2 text-[1.1rem]">
                <span className="text-white">✓</span> {point}
              </li>
            ))}
          </ul>
        </div>

        {/* Always at bottom */}
        <div className="mt-6">
          {item.id === 1 ? (
            <Button className="cursor-pointer"><Link href={'/farmer/vehicle-request'}>बुक करें</Link></Button>
          ) : (
            <RegisterLink>
              <Button className="cursor-pointer">रजिस्टर करें</Button>
            </RegisterLink>
          )}
        </div>
      </div>
    </Card>
  );
};

export default DropCard;
