import { Meta } from "@once-ui-system/core";
import { baseURL, tracks } from "@/resources";
import { TrackHome } from "@/components/TrackHome";

export async function generateMetadata() {
  return Meta.generate({
    title: tracks.research.title,
    description: tracks.research.description,
    baseURL: baseURL,
    path: tracks.research.path,
    image: "/images/og/home.jpg",
  });
}

export default function ResearchHome() {
  return <TrackHome track="research" />;
}
