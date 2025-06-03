import "../globals.css";
import { NavMenu } from "../_components/navmenu";
import { Header_vencimento } from "../_components/venc_header";
import { Vencimento } from "../_components/consulta_vencimento";

export default function _Validade() {
    return (
        <>
            <NavMenu />
            <Header_vencimento />
            <Vencimento />
        </>
    );
}