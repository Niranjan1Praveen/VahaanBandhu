
import Features from '@/sections/Features'
import Footer from '@/sections/Footer'
import Hero from '@/sections/Hero'
import Introduction from '@/sections/Introduction'
import Navbar from '@/sections/Navbar'
import SignUpOptions from '@/sections/SignupOptions'
import React from 'react'


const Home = () => {
  return (
    <>
        <Navbar/>
        <Hero/>
        <Introduction/>
        <Features/>
        <SignUpOptions/>
        <Footer/>
    </>
  )
}

export default Home;