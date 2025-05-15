import "./globals.css";
import { NavMenu } from "./_components/navmenu";
import { Consulta } from "./_components/consulta";

export default function Home() {
    return (
        <>
            <NavMenu />
            <Consulta />
        </>
    );
}