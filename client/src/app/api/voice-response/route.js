import prisma from "@/app/utils/db";
import { NextResponse } from "next/server";

export async function POST(req) {
  try {
    const body = await req.json();
    const { crop, market, quantity, latitude, longitude } = body;

    if (!crop || !market || !quantity) {
      return NextResponse.json({ error: "Missing fields" }, { status: 400 });
    }

    const response = await prisma.VoiceResponse.create({
      data: {
        crop,
        market,
        quantity,
        Latitude: latitude ?? null,
        Longitude: longitude ?? null,
      },
    });

    return NextResponse.json({ success: true, data: response });
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: "Failed to save response", details: error.message },
      { status: 500 }
    );
  }
}
