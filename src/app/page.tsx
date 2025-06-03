import "./globals.css";
import { NavMenu } from "./_components/navmenu";
import { Header } from "./_components/header";
import { Consulta } from "./_components/consulta";

export default function Home() {
    return (
        <>
            <NavMenu />
            <Header />
            <Consulta />
        </>
    );
}