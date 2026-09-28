import { Meta } from "@once-ui-system/core";
import { baseURL, tracks } from "@/resources";
import { TrackHome } from "@/components/TrackHome";

export async function generateMetadata() {
  return Meta.generate({
    title: tracks.finance.title,
    description: tracks.finance.description,
    baseURL: baseURL,
    path: tracks.finance.path,
    image: "/images/og/home.jpg",
  });
}

export default function FinanceHome() {
  return <TrackHome track="finance" />;
}
