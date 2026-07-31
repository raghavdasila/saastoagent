import { Menu } from "lucide-react";
import { useRouteDeckCurrentNode } from "@routedeck/react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export interface ApplicationNavigationDrawerProps {
  navigation: ReactNode;
}

export function ApplicationNavigationDrawer({
  navigation,
}: ApplicationNavigationDrawerProps) {
  const currentNode = useRouteDeckCurrentNode();
  const loungeActive = currentNode?.startsWith("lounge.") ?? false;
  const title = loungeActive ? "Lounge navigation" : "Workspace navigation";
  const description = loungeActive
    ? "Public Corpus locations and account paths."
    : "Corpus features and application areas.";

  return (
    <div data-application-navigation-mobile="">
      <Sheet>
        <SheetTrigger asChild>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            aria-label="Open navigation menu"
          >
            <Menu />
          </Button>
        </SheetTrigger>
        <SheetContent
          side="left"
          className="w-[min(88vw,360px)] gap-0 overflow-y-auto p-0 sm:max-w-[360px]"
        >
          <SheetHeader className="border-b px-5 py-5">
            <SheetTitle>{title}</SheetTitle>
            <SheetDescription>{description}</SheetDescription>
          </SheetHeader>
          <nav aria-label={loungeActive ? "Lounge sections" : "Workspace sections"} data-application-navigation-drawer="">
            {navigation}
          </nav>
        </SheetContent>
      </Sheet>
    </div>
  );
}
