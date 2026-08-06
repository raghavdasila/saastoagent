import { useRouteDeckContract, useRouteDeckCurrentNode } from "@routedeck/react";
import { Bot, DatabaseZap, House, KeyRound, LogIn, MailCheck, MessageCircleQuestion, UserPlus } from "lucide-react";

const NODE_PRESENTATION = Object.freeze({
  "lounge.home": { icon: House, detail: "Public starting point" },
  "lounge.product_help": { icon: MessageCircleQuestion, detail: "Ask about Corpus" },
  "lounge.sign_in": { icon: LogIn, detail: "Existing account" },
  "lounge.register": { icon: UserPlus, detail: "New account" },
  "lounge.forgot_password": { icon: KeyRound, detail: "Password recovery" },
  "lounge.reset_password": { icon: KeyRound, detail: "Set a new password" },
  "lounge.verify_email": { icon: MailCheck, detail: "Confirm email" },
  "lounge.verification_pending": { icon: MailCheck, detail: "Verification delivery" },
  "workspace.home": { icon: House, detail: "Owner Workspace" },
  "agents.home": { icon: Bot, detail: "Agent inventory" },
  "agents.create": { icon: Bot, detail: "Create an agent" },
  "sources.home": { icon: DatabaseZap, detail: "Connector debug" },
});

const PUBLIC_LOUNGE_NODES = new Set(["lounge.home", "lounge.product_help"]);

export function FeatureNavigation() {
  const contract = useRouteDeckContract();
  const currentNode = useRouteDeckCurrentNode();
  const nodes = Object.values(contract.nodes);
  const loungeActive = currentNode?.startsWith("lounge.") ?? false;
  const loungeNodes = nodes.filter(
    (node) =>
      node.id.startsWith("lounge.") &&
      (PUBLIC_LOUNGE_NODES.has(node.id) || node.id === currentNode),
  );
  const groups = loungeActive
    ? [{ title: "Lounge", nodes: loungeNodes }]
    : [
        { title: "Workspace", nodes: nodes.filter((node) => node.id.startsWith("workspace.")) },
        { title: "Agents", nodes: nodes.filter((node) => node.id.startsWith("agents.")) },
        { title: "Sources", nodes: nodes.filter((node) => node.id.startsWith("sources.")) },
      ];

  return (
    <div className="workspace-navigation">
      <h2>Features</h2>
      {groups.map((group) => (
        <section key={group.title} className="workspace-navigation-group">
          <h3>{group.title}</h3>
          <ul>
            {group.nodes.map((node) => {
              const presentation = NODE_PRESENTATION[node.id as keyof typeof NODE_PRESENTATION];
              const Icon = presentation?.icon ?? House;
              return (
                <li key={node.id} data-current={node.id === currentNode ? "true" : "false"}>
                  <span aria-hidden="true"><Icon /></span>
                  <div>
                    <strong>{node.title}</strong>
                    <small>{presentation?.detail ?? group.title}</small>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
