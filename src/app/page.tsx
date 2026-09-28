import { redirect } from "next/navigation";
import { tracks } from "@/resources";

// The site has two tracks; finance is the default landing.
// The switcher on /finance and /research moves between them.
export default function Home() {
  redirect(tracks.finance.path);
}
