# 5

# Conversational Interfaces

Conversational interfaces are becoming an essential layer in modern platform engineering. As platforms grow more capable and incorporate organizational knowledge, developers need easier ways to interact with them, especially when navigating **infrastructure** ** as code ** ( **IaC** ), CI/CD pipelines, or standardized service templates. Instead of relying on documentation or searching through repositories, developers can now describe what they want in natural language and let the platform guide them.

These interfaces introduce a more intuitive way for teams to adopt platform capabilities, discover paved roads, and generate consistent artifacts without memorizing patterns or low-level details. When combined with organizational context, conversational tools help developers start tasks faster, explore solutions more freely, and align with platform standards from the very beginning.

In this chapter, we explore how conversational interfaces enhance platform engineering workflows and how they integrate with systems such as the **Model** **Context** **Protocol** ( **MCP** ) to access platform capabilities programmatically. Through practical examples, we'll examine how AI-assisted interactions surface the right templates, pipelines, and configurations while reinforcing consistency and reducing cognitive load.

It helps to name the implementation boundary early, because conversational systems differ sharply in how far they are permitted to go. Such a system might only discover and explain what already exists; it might generate artifacts for a human to review; it might propose a change through an existing approval workflow; or it might execute directly against the environment. Each step widens the blast radius, and each demands more of the surrounding governance. The system we build in this chapter stops at discovery, explanation, and proposal. Every change that reaches the cluster does so through a pull request, and a human merges it.

In this chapter, we're going to cover the following topics:

* Overview of conversational AI tools for platform engineering
* Integrating conversational interfaces with the Model Context Protocol (MCP)
* Practical demo: AI-assisted platform tasks
* Limitations of current AI tools in platform engineering
* The case for embedded knowledge structures

By the end, you'll understand how conversational AI becomes an extension of your internal platform, enabling intent-driven workflows that support both productivity and standardization.

# Technical requirements

The demo in this chapter builds a working developer portal and connects it to a live Kubernetes cluster. Everything runs locally on a single machine, so you do not need a cloud account for the platform itself. The only external dependency is the model provider behind the chat assistant.

To follow along, you need:

* Docker, `kind`, and `kubectl`. The setup script creates a local `kind` cluster named `agentic‑platform`, with Metrics Server and Argo CD installed on it.
* Node.js 22.x. The scaffolder backend depends on `isolated‑vm`, which does not build on newer releases.
* Yarn 4.x, enabled through Corepack.
* A GitHub account and a fine-grained personal access token with read and write access to contents and pull requests.
* An AWS account with Amazon Bedrock access, or an OpenAI API key.

The versions below are the ones this chapter was written and tested against. Backstage moves quickly, and these labs deliberately pin versions rather than track the latest release:

* Backstage scaffolded with `@backstage/create‑app` 0.7.9, with all `@backstage/*` packages pinned to release 1.48.0
* `@aws/genai‑plugin‑for‑backstage` 0.5.0 and `@aws/genai‑plugin‑for‑backstage‑backend` 0.7.1
* `@aws/genai‑plugin‑langgraph‑agent‑for‑backstage` 0.7.2
* `@backstage/plugin‑mcp‑actions‑backend` 0.1.9
* Argo CD v3.0.21

These version constraints matter. Versions 0.8.x and later of `create‑app` scaffold Backstage's new frontend system, and the file edits in this chapter will not apply to them. Backstage releases 1.49.0 and later declare a service reference that no current factory provides, which prevents the catalog, scaffolder, and MCP actions plugins from starting. The MCP actions backend pin follows from that same constraint: releases 0.1.10 and later carry the requirement and fail the same way, so 0.1.9 is the last release that starts on 1.48.0.

The cluster is created once and reused by every lab in the chapter:

```
cd 00-cluster-setup
./setup-cluster.sh
./verify.sh
```

The script is idempotent, so re-running it is safe. It creates the cluster, installs Metrics Server, and installs Argo CD. Rather than reproduce every step here, we keep the instructions in the repository, where they are maintained alongside the code. The full setup guide, including Amazon EKS notes, the Argo CD admin password, and teardown instructions, is at:

[`https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/00-cluster-setup](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/00-cluster-setup)`

A note on Amazon Bedrock before you start. Access to foundation models is enabled by default in commercial AWS Regions when the account has the required AWS Marketplace permissions, although Anthropic first-time users may need to submit use case details. Model availability and supported inference profiles vary by Region. This chapter invokes Anthropic's Claude Sonnet 4.5 from `us‑west‑2` using the global cross-Region inference profile; if you use another source Region or inference profile, confirm that the model and profile are supported there and adjust the configuration accordingly.

Cost is worth stating plainly, because readers following along will be billed. The `kind` cluster is free, which is why we default to it. Bedrock charges per token consumed, and the traffic generated by this chapter is small: a handful of conversations at most. If you substitute a managed cluster such as Amazon EKS, you are billed hourly for as long as that cluster exists, so remember to tear it down when you are finished.

All code for this chapter, including the cluster setup script and the four labs, is in the book's repository under the `chapter‑05` directory. The walkthrough tracks the main branch, the state against which every command and version listed above was tested:

[`https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05)`

# Overview of conversational AI tools for platform engineering

As we saw in the introduction, conversational interfaces offer a more natural way for developers to access and use platform capabilities. To understand why this shift is meaningful, it helps to revisit one of the most important abstractions in modern platform engineering: Kubernetes Operators.

Operators changed how teams encoded operational knowledge. Instead of relying solely on scripts, runbooks, or human intervention, Operators extended Kubernetes's controller pattern with domain-specific operational knowledge, continuously comparing the *desired state* defined by the user with the *actual state* running in the cluster. When the two didn't match, the Operator took corrective action automatically.

At their core, Operators allow developers to communicate intent:

* "I want a database that looks like this."
* "I want a message queue with these characteristics."
* "I want a cluster add-on configured in this way."

Operators accept declarative resources, defined through custom resource definitions (CRDs), that describe higher-level concepts and translate that intent into the low-level operational steps needed to implement it. The user doesn't manage backups, replicas, or failover logic; the Operator handles that complexity. *Figure 5.1* illustrates this reconciliation pattern.

![](./imgs/B34160_5_1.png)

Figure 5.1: The Kubernetes Operator pattern: a user declares intent in a custom resource, and the Operator adjusts the cluster to match

This shift from instructing the system step-by-step to simply describing the desired state marked a turning point in platform engineering. It demonstrated that intent is a powerful abstraction: once the platform understands what you want, it can automate the rest.

Conversational AI tools extend this same philosophy to how developers interact with the platform in their day-to-day work. Instead of expressing intent through YAML or CRDs, developers express it through natural language. Tools such as Kiro, GitHub Copilot, and Anthropic Claude bring this capability directly into integrated development environments (IDEs), terminals, or chat interfaces.

These tools occupy different positions in a platform workflow, and the distinction is more useful than any feature comparison. Kiro is the agentic development environment AWS now offers, built around spec-driven development: instead of responding prompt by prompt, it works from a written specification that it then implements, which suits platform work where the intended change is known in advance and consistency matters more than speed. GitHub Copilot is anchored in the repository and the pull request, so it fits naturally where platform work looks like code review and scaffolding. Anthropic's Claude is available through IDEs, a command line interface, and an API, and its support for MCP makes it a common choice when a platform team wants to expose its own systems as tools rather than adopt a fixed integration set.

The benefit these tools share in a platform context is not code generation as such. It is that a developer can start from a question rather than from a blank file and receive an answer shaped by the organization's own conventions. Typical uses are scaffolding a service that already matches platform standards, explaining an unfamiliar manifest or module, and finding the approved way to do something without reading the whole internal documentation set.

One caution before we go further. Product capabilities and integrations in this space change quickly, and any specific claim about what a given tool supports has a short shelf life. The patterns in this chapter outlast the products that implement them: grounding a model in organizational knowledge, exposing platform capabilities as narrow tools, and routing changes through existing approval workflows. Where we name a tool, check its official documentation for current behavior.

That caution is not hypothetical. If you have previously used Amazon Q Developer, which earlier material on this topic frequently names, Kiro is where that line of work continues. AWS has announced the end of support for the Q Developer IDE plugins and paid subscriptions. New sign-ups closed on May 15, 2026, and support for the existing IDE plugins ends on April 30, 2027. Amazon Q Developer in the AWS Management Console and in Slack and Microsoft Teams is not affected by that change. We name Kiro because it is the current offering, but the pattern being described here long outlives either name.

What makes these tools effective in platform engineering is their ability to merge two essential types of context:

* **Local ****c** **ontext** **:** the project structure, languages, configuration files, and dependencies in the developer's workspace.
* **Organizational ****k** **nowledge** **:** conventions, IaC modules, platform templates, architectural standards, and golden paths captured by the platform team (as discussed in  *[Chapter 4](https://learning.oreilly.com/library/view/agentic-ai-for/9781806386659/Chapter_4.xhtml#h1_79)* ).

When these sources are combined, conversational interfaces can translate a developer's intent into scaffolding, configuration, or automation that aligns with the organization's standards, just as Operators translate declarative intent into operational actions inside Kubernetes.

This means developers no longer start with a blank file or search manually for "the right example." They begin by expressing what they want, and the platform provides a grounded, standards-aligned starting point. For platform teams, this makes paved roads easier to discover, reduces support overhead, and helps maintain consistency at scale.

Conversational AI becomes, in many ways, the user-facing equivalent of an Operator: a mechanism that receives intent, applies knowledge, and produces the structure required to make that intent real. The analogy is useful, but it should not be pushed too far. An Operator reconciles continuously and deterministically toward a declared state; a conversational system produces a proposal, and that proposal can vary between runs. The resemblance is in the shape of the interaction, not in the guarantees. This is why the conversational layer belongs in front of controlled workflows rather than in place of them, and why every change in this chapter reaches the cluster through a reviewed pull request.

# Integrating conversational interfaces with the Model Context Protocol (MCP)

Conversational interfaces depend on more than language understanding. They also need a reliable way to interact with platform systems in a predictable and governed manner. The Model Context Protocol provides a standard way to expose such capabilities to MCP clients. While a conversational interface interprets intent and converts natural language into structured requests, an MCP server can expose platform actions and context through a governed protocol boundary.

Earlier we explored how MCP allows an AI system to retrieve organizational knowledge such as templates, service definitions, architectural patterns, and configuration standards. This retrieval capability helps ensure that the conversational interface produces suggestions that reflect how the organization expects resources to be built. Retrieval, however, is only one side of MCP. MCP can also expose tools that let an AI invoke controlled platform actions.

At the core of MCP is the concept of a  **tool** . A tool represents a specific capability that the platform team chooses to expose. Each tool defines what it can do, the inputs it expects, and the validation steps required before an action is executed. These definitions support safer conversational automation because each operation passes through an explicitly registered capability that can be validated and governed.

Tools are the primitive we use most in this chapter, but they are not the whole of MCP, and conflating the two leads to thinking of the protocol as little more than a standard way to call functions. MCP defines three primitives. Tools are actions the model can invoke, and they may have side effects. Resources are read-only context the server makes available for the model to consult. The retrieval described a moment ago maps more naturally onto resources than onto tools. Prompts are reusable, parameterized templates that a server can offer to standardize how a particular request is phrased. A platform team decides which of these to expose, and the distinction matters because the safety questions differ: a resource discloses information, while a tool acts.

It is also worth clarifying which component plays each role, since the terms recur throughout the chapter. In MCP, the host is the application the user interacts with, the client is the component inside the host that manages protocol connections, and the server exposes tools, resources, or prompts. In this chapter, Backstage registers the actions once: the in-portal assistant consumes selected actions directly from the registry, while the MCP actions backend exposes those same actions to external MCP clients.

Authentication and authorization belong at the platform-side tool boundary, not in the model. This is the part most worth internalizing. The model produces a request to call a tool; it should not hold platform credentials or reach a platform system directly. Whether that call is permitted, and with what identity it executes, is decided at the backend action or MCP server boundary, where authorization and audit controls can be enforced. We return to exactly how that plays out, including its limitations, when we connect the assistant to the cluster later in this chapter. *Figure 5.2* illustrates this agent-to-server relationship.

![](./imgs/B34160_5_2.png)

Figure 5.2: An agent reaching platform capabilities through MCP servers, each exposing a narrow, explicitly defined set of tools

When a conversational system generates Terraform files, Kubernetes manifests, or other artifacts, it could apply those changes directly to the environment. However, in this book we focus on approaches that preserve existing deployment strategies and governance models. One option is to expose an MCP tool that creates a branch, commits the generated resources, and opens a pull request. That is exactly the tool an agent receives in  *[Chapter 7](https://learning.oreilly.com/library/view/agentic-ai-for/9781806386659/Chapter_7.xhtml#h1_142)* . The assistant we build later in this chapter stops one step short and stays read-only, so that the write path can be examined on its own.

The organization's continuous integration workflows then run the usual validations, including tests, policy checks, and security scans. After the pull request is approved and merged, the deployment step is carried out through the organization's existing delivery approach. This may involve GitOps controllers detecting the change and applying it automatically, or a more traditional continuous deployment pipeline. The key point is that changes created through the conversational interface follow the same controlled and auditable path as every other modification.

Platform teams can also provide a hosted conversational interface. The hosted interface removes the need for developers to install plugins or configure local environments. A hosted interface centralizes authentication, authorization, organizational knowledge, and governance. Conversation auditability still depends on the logging, retention, identity, and access controls configured by the platform team.

To understand how MCP and conversational interactions work together, consider an illustrative example: a developer who needs to deploy a three-tier application. This walkthrough is a conceptual one, meant to show how the pieces fit; it is not the exercise you will build later in this chapter, and we do not return to it. The developer opens the hosted conversational interface and describes the requirements: an API layer, a backend service, and a database with specific scaling and security constraints. *Figure 5.3* shows the developer starting with a natural-language description of the application.

![](./imgs/B34160_5_3.png)

Figure 5.3: A developer describing a three-tier application in natural language rather than authoring the manifests directly

The conversational interface interprets the request and uses retrieval-augmented generation (RAG) and MCP to pull together the organization's templates, reference architectures, and standards. With that context, it generates the required resource manifests and applies all naming conventions, tags, and security requirements automatically. After the platform assembles the final set of resources, MCP tools commit the generated files to the appropriate repository and open a pull request. *Figure 5.4* summarizes this conceptual flow.

![](./imgs/B34160_5_4.png)

Figure 5.4: The full conversational path, with an agent reaching a knowledge base, a cloud provider, and Git through separate MCP servers

From there, the organization's CI/CD process evaluates the change and, once approved, carries it through the usual release workflow. This model shows how conversational intent fits naturally into the platform's existing delivery practices. The developer communicates what they need, and the platform uses its established knowledge, governance, and automation to produce a safe, consistent outcome. The interaction begins with natural language but ends as a standard, fully governed platform update.

# Practical demo: AI-assisted platform tasks

In this practical demo, we walk through a realistic platform engineering setup and gradually introduce conversational capabilities. Rather than starting with AI, we begin with a familiar, production-ready baseline and then layer intelligence on top. This makes it easier to see what conversational interfaces add, and why they are most effective when integrated into existing platform workflows.

It is worth setting expectations about what this demo does and does not cover. The platform tasks on display are infrastructure-as-code generation and service scaffolding: the Backstage template produces a complete set of Kubernetes manifests (a Deployment, Service, ConfigMap, and horizontal pod autoscaler) along with the Argo CD application that delivers them, and it does so through a pull request rather than by writing to the cluster. The conversational layer we build on top makes that paved road discoverable and explains what is running once it is deployed. Authoring CI/CD pipeline definitions and AI-assisted linting are adjacent uses of the same techniques, and they follow the same pattern of grounding plus a governed write path, but we do not build them here.

## Establishing the platform baseline with Backstage and GitOps

We begin by establishing a platform engineering baseline using Backstage as the developer portal and GitOps as the deployment model. This baseline reflects how many platform teams structure their internal platforms today and serves as a stable reference point for introducing conversational capabilities later in this chapter. *Figure 5.5* shows the Backstage template catalog used in the demo.

![](./imgs/B34160_5_5.png)

Figure 5.5: The Backstage template catalog, showing the Web App with Kubernetes Deployment template used in this demo

Backstage acts as the primary interface for developers, providing service discovery, standardized templates, and a consistent entry point into the platform. Rather than interacting directly with infrastructure or deployment tooling, developers express intent through Backstage, such as creating a new service or discovering existing components.

All platform changes are managed through Git. When a developer creates a new application from a Backstage template, the resulting configuration is committed to a Git repository and reviewed through a pull request. This ensures that governance, auditability, and collaboration remain aligned with existing engineering practices. *Figure 5.6* shows the resulting pull request.

![](./imgs/B34160_5_6.png)

Figure 5.6: The pull request opened by the Backstage template, carrying the generated Kubernetes manifests

Deployments are handled by Argo CD, a GitOps controller that continuously reconciles the desired state defined in Git with the actual state running in the Kubernetes cluster. Instead of triggering deployments manually, changes become active simply by merging pull requests. We use Argo CD here because its `ApplicationSet` controller can discover new applications in the components repository automatically, so a service scaffolded from a template deploys without anyone registering it by hand. If your organization runs Flux, the same outcome is reachable, but the substitution is not one-to-one. Flux splits the job across a `GitRepository`, which declares the source, and one or more `Kustomization` resources, which reconcile paths within it, and it has no counterpart to the `ApplicationSet` git generator. The per-application discovery this chapter leans on therefore has to be rebuilt, either as a top-level `Kustomization` that lists every application directory, or as a Flux `Kustomization` committed for each application and reconciled by a parent. Each application would also need its own `Namespace` manifest, because Flux does not create namespaces the way the `CreateNamespace` sync option does here, and the repository credentials take a different secret shape. The labs target Argo CD only. This model reinforces a clear separation of concerns: Backstage captures intent, Git represents desired state, and the cluster converges automatically. *Figure 5.7* shows the resulting application synced and healthy in Argo CD.

![](./imgs/B34160_5_7.png)

Figure 5.7: Argo CD showing my-first-app synced and healthy after the pull request is merged

Application templates define how services are structured, deployed, and registered in the platform. A Kubernetes-based web application template is used to demonstrate this flow end to end, including service registration in Backstage and automated deployment through GitOps. Once deployed, services become visible both in the cluster and in the developer portal, closing the feedback loop between creation and operation.

This baseline is intentionally free of AI or conversational features. Its purpose is to establish a clear, well-understood platform workflow that many organizations already recognize. Starting from this familiar foundation makes it easier to see what conversational interfaces add, and why they are most effective when layered on top of existing platform abstractions rather than introduced in isolation.

 **Practical reference** :

The complete setup for this baseline, including Backstage configuration and GitOps integration, is available in the following repository:

`[github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/1-backstage-setup](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/1-backstage-setup)`

## Adding a conversational interface to Backstage

With the platform baseline in place, we introduce a conversational interface into Backstage. The goal of this step is not to create a fully capable platform assistant, but to establish the simplest possible AI interaction surface inside the developer portal.

Using the AWS GenAI plugin for Backstage, we add an AI-powered chat interface that developers can access directly from the portal's navigation. This chat assistant is backed by a **large language model** ( **LLM** ), such as an Amazon Bedrock-hosted model or an alternative provider like OpenAI. At this stage, the assistant operates purely as a general-purpose conversational interface.

Concretely, that means three backend packages and one frontend package. The backend uses `@aws/genai‑plugin‑for‑backstage‑backend`, which provides the chat API, `@aws/genai‑plugin‑langgraph‑agent‑for‑backstage`, which supplies the agent implementation, and `@backstage/plugin‑mcp‑actions‑backend`, which provides the actions registry that both depend on. The registration order matters: the actions registry has to be added before the GenAI plugins, or they will fail to resolve it at startup. The frontend uses `@aws/genai‑plugin‑for‑backstage`, which supplies the chat page component and the sidebar entry. *Lab 2* in the repository lists the exact commands and file edits.

The model provider is set in `app‑config.yaml`, under the agent's `langgraph` block, and switching provider means replacing one nested key. The configuration used here selects Amazon Bedrock:

```
genai:
  agents:
    general:
      langgraph:
        messagesMaxTokens: 150000
        bedrock:
          modelId: 'global.anthropic.claude-sonnet-4-5-20250929-v1:0'
          region: us-west-2
```

The complete configuration, including the OpenAI variant, the exact install commands, and the file edits to App.tsx and Root.tsx, is in Lab 2 in the repository:

`[github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/2-add-chat-assistant](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/2-add-chat-assistant)`

Replacing the `bedrock` block with an `openai` block, which takes an `apiKey`, moves the assistant to OpenAI without requiring any other changes in the chapter. Nothing else in the walkthrough depends on the provider: the catalog actions, the Kubernetes actions, and the governance model all sit above it. Readers on Azure or Google Cloud, or running a self-hosted model, should expect to make the substitution at this same key rather than elsewhere, though the plugin's supported providers are worth checking against its documentation before committing to one.

One note on maturity is warranted because this plugin is going into a portal used by an entire engineering organization. The GenAI plugins are maintained by AWS Labs as part of the `backstage‑plugins‑for‑aws` project. They are actively developed and still below version 1.0, which is why this chapter pins exact versions rather than tracking the latest release. Treat the plugin as you would any other pre-1.0 dependency in a shared system: pin it, watch its changelog, and test upgrades before they reach developers. *Figure 5.8* shows the assistant before platform-specific actions are added.

![](./imgs/B34160_5_8.png)

Figure 5.8: The chat assistant before any platform integration, unable to answer which services exist

From a platform perspective, this is an intentionally constrained setup. The assistant can answer general questions about software development, cloud concepts, or platform engineering practices, and it responds using structured, well-formatted Markdown. However, it has no awareness of the organization's internal platform, services, repositories, or runtime environments.

This limitation is deliberate and important. The assistant is not connected to Backstage's catalog, documentation, or any operational systems. Its responses are based solely on the model's training data and the static prompt provided during configuration. As a result, while it can be useful for learning or exploration, it cannot reliably support platform-specific workflows.

Introducing the conversational interface in this isolated form makes a key point visible early: conversational AI alone is not sufficient for platform engineering. Without access to organizational context, the assistant cannot answer questions such as which services exist, who owns them, or what is currently running in the cluster. This gap highlights the difference between a generic chatbot and a platform-aware assistant.

At the same time, embedding the chat interface directly into Backstage is a crucial architectural decision. By placing the conversational entry point inside the developer portal, we ensure that future capabilities build on existing platform abstractions rather than exist as a separate tool. Developers do not need to switch contexts or adopt a new interface; the assistant becomes a natural extension of the platform itself.

This step establishes the conversational foundation. In the next section, we begin closing the context gap by connecting the assistant to Backstage's service catalog, allowing it to reason about real platform entities instead of abstract concepts.

 **Practical reference** :

Step-by-step instructions for enabling the conversational interface in Backstage can be found here:

`[github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/2-add-chat-assistant](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/2-add-chat-assistant)`

## Enriching the chat assistant with Backstage catalog knowledge

After introducing a conversational interface in isolation, the next step is to give the assistant awareness of the platform itself. We do this by connecting the chat assistant to Backstage's software catalog and documentation systems.

At this stage, the assistant is extended with a small set of built-in Backstage actions that allow it to query catalog entities and search technical documentation. These actions provide read-only access to the same sources of truth that developers already use through the Backstage UI, such as registered components, ownership metadata, and TechDocs content.

With this integration in place, the assistant can begin reasoning about real platform entities instead of abstract concepts. Developers can ask which components exist, who owns a service, or what details are available about a specific application. The assistant can also search technical documentation to answer questions using information already captured in TechDocs, surfacing relevant information without requiring developers to manually navigate documentation pages. *Figure 5.9* shows the assistant answering from catalog-backed context.

![](./imgs/B34160_5_9.png)

Figure 5.9: The assistant answering from real catalog entities after the Backstage actions are registered

This represents a meaningful shift in capability. The assistant is no longer a generic chatbot; it becomes platform-aware. Its responses are grounded in organizational knowledge that reflects how the platform is structured and documented. Importantly, this knowledge is curated and governed: the catalog and TechDocs are already maintained as part of normal platform operations, so the assistant can reuse those same controls and conventions.

However, this view of the platform is still incomplete. The Backstage catalog describes what *should* exist: registered services, intended ownership, and documented behavior. It does not represent the live state of the platform. The assistant cannot yet answer questions about whether a service is currently deployed, healthy, or running in a specific environment.

This distinction is intentional. By first enriching the assistant with catalog knowledge, we establish a clear separation between *declared platform structure* and  *runtime reality* . This makes it easier to understand the role each integration plays as the assistant evolves.

At this point, the conversational interface supports discovery and understanding, but not operations. In the next section, we extend the assistant beyond static metadata by registering a second set of actions that provide read-only views of the live cluster.

 **Practical reference** :

The configuration used to connect the chat assistant with the Backstage catalog is available at: `[https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/3-add-catalog-actions](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/3-add-catalog-actions)`

## Extending the chat assistant with MCP and cluster awareness

Up to this point, the conversational interface has been grounded in static, declared knowledge. By connecting the assistant to the Backstage catalog and documentation, it can reason about what *should* exist in the platform. The next step is to extend this view with awareness of what is  *actually running* .

To achieve this, we register four custom actions in Backstage's actions registry, the same registry that already holds the catalog and TechDocs actions. Registering them once gives us two ways in. The first is our assistant: we list the actions by name under the agent's `actions` key in `app‑config.yaml`, and the GenAI plugin resolves them and hands them to the model as tools, in process, with no protocol in between. The second is the MCP server that the MCP actions backend runs over HTTP, which publishes those same actions to any MCP-native client outside the portal. That second door is worth dwelling on, because it determines who can use what you built. The platform's capabilities stop being something a developer has to open the catalog to reach; they become available in the editor or the terminal where the work is already happening. *Lab 4* concludes by doing exactly that, calling `kubectl_get_pods` from a client that is not Backstage at all. The package is here because it provides the registry factory the GenAI plugin depends on, as we saw when installing it, and because our Kubernetes module attaches to it: the module registers under the `mcp‑actions` plugin ID, which is why that name appears in `pluginSources`. Whichever door the model comes through, the contract is the same. Each action exposes one narrowly scoped, read-only capability, such as listing workloads or describing a resource, rather than exposing arbitrary command-line access.

Through this integration, the assistant can query Kubernetes for authoritative runtime data. It can list pods, deployments, and services within a namespace, or inspect the state of a specific workload. This shifts the assistant from a documentation and discovery tool into an operationally aware interface that reflects the current state of the platform.

On the assistant's side, the whole integration is this binding:

```
backend:
  actions:
    pluginSources: [catalog, aws-genai, mcp-actions]
genai:
  agents:
    general:
      actions:
        - get-catalog-entity
        - search-catalog
        - search-techdocs
        - kubectl_get_pods
        - kubectl_get_deployments
        - kubectl_get_services
        - kubectl_describe_pod
```

An action that is registered but not listed here is invisible to the model. If the assistant says it cannot do something you expected it to, this list is the first place to look.

Each action is a small, explicit contract. The definition states the tool's name, what it does, the inputs it accepts, and the shape of what it returns; the model can only call it in those terms. The pod listing action, for example, declares one input, a namespace, and one output: an object that carries the `kubectl` result as a string:

```
actionsRegistry.register({
  name: 'kubectl_get_pods',
  title: 'Get Kubernetes Pods',
  description: 'Get pods in a Kubernetes namespace',
  schema: {
    input: (zod) => zod.object({
      namespace: zod.string().default('default'),
    }),
    output: (zod) => zod.object({
      result: zod.string(),
    }),
  },
  action: async ({ input }) => {
    const result = await execKubectl([
      'get', 'pods', '-n', input.namespace, '-o', 'json',
    ]);
    return { output: { result } };
  },
});
```

That is an abbreviated view; the repository version also attaches a description to each field, which is what the model reads when deciding how to call it. The registry validates the return value against the output schema, which is why the action wraps the string rather than returning it bare. The full module, which registers all four actions and handles the `kubectl` invocation, is a single TypeScript file in the repository, and *Lab 4* provides step-by-step instructions for adding it:

[`https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/4-add-kubernetes-actions](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/4-add-kubernetes-actions)`

One caveat is worth knowing before you open that endpoint anywhere real. The MCP surface publishes what the registry holds, not the shorter list the agent is bound to, so it can expose more than your assistant can reach. In the setup in this chapter, the agent has seven read-only actions while the endpoint advertises thirteen, including two that write to the catalog. Read the tool list before you hand anyone the token, and scope it the way you would scope any other credential.

There is no free-form command parameter anywhere in that definition, which is the point. The assistant cannot construct an arbitrary `kubectl` invocation, because the only thing it controls is the namespace string. Widening what the assistant can do means registering another action and reviewing it, which is a deliberate act by the platform team rather than a side effect of how a request happens to be phrased.

Two caveats matter before anyone runs this beyond a demo. The first is identity. In this implementation, the action runs `kubectl` from the Backstage backend, which means every request reaches the cluster as the backend's own identity, not as the developer who asked the question. On the local cluster used here that is unremarkable. In a shared environment it is significant: any developer who can open the chat can see whatever the backend is permitted to see, which means the developer's Kubernetes permissions are not applied; every request is authorized as the backend identity instead. A production deployment would bind the backend to a dedicated service account scoped to the smallest useful set of resources and would carry the requesting user's identity through to the cluster call so that existing permissions continue to apply.

The second is that read-only is not the same as safe. A role that can read pods can usually read pod specifications, and those routinely contain environment variables, mounted secret names, and connection strings. Anything the assistant reads may end up in a chat transcript, and chat transcripts are frequently logged. When scoping the service account, exclude secrets outright, and treat the ability to describe pods as a disclosure decision rather than a convenience. *Figure 5.10* shows the live pod-status result returned through the read-only action.

![](./imgs/B34160_5_10.png)

Figure 5.10: The assistant reporting live pod status retrieved through the kubectl_get_pods action

This distinction is critical. Runtime awareness closes the gap between intent and reality. The assistant no longer relies on assumptions derived from templates or catalog entries; instead, it retrieves information directly from the cluster through approved actions. As a result, developers can ask questions about whether an application is deployed, whether workloads are healthy, or where a service is running, and receive answers based on live platform state.

Equally important is how this access is implemented. The boundary between the language model and the platform is the actions registry, whether the model reaches it in process, as ours does, or through the MCP endpoint, as an external client would; MCP is the standardized form that boundary takes when it has to cross a network. Actions are explicitly registered, validated, and governed, so the assistant can only perform the operations it has been authorized to perform. Here those operations are intentionally read-only, which keeps the assistant observational while still delivering useful operational insight. *Figure 5.11* shows what that boundary looks like from the developer's side when a request falls outside it.

![](./imgs/B34160_5_11.png)


Figure 5.11: The assistant declining to modify a deployment because no write action is registered

*Figure 5.11* is the most important screenshot in this chapter, and it is worth reading carefully, because at first glance it looks like a failure. A developer asks the assistant to change a deployment's CPU limits, and the assistant declines. It declines because no tool exists that would let it comply: the only Kubernetes actions registered are read operations. This is the guardrail working exactly as designed. The model is not deciding to be cautious, and it is not being restrained by an instruction in its prompt that a cleverly worded request might circumvent. The capability simply is not there.

One detail in that response does deserve correction. The assistant suggests `kubectl patch` and `kubectl edit` as the way to make the change. Those commands would work, but they are the wrong remediation path for this platform: an imperative edit to the cluster would be silently reverted the next time Argo CD reconciled against Git, and it would leave no record in the repository that anyone can review. The correct route is a pull request against the manifests, which is exactly what the next section describes. It is a useful reminder that a model grounded in general knowledge will reach for the general answer unless the platform gives it a better one.

At this stage, the conversational interface becomes a true operational assistant. It combines organizational knowledge from the Backstage catalog with real-time platform state from Kubernetes, all surfaced through a single natural-language interface inside the developer portal.

However, the assistant is still observational. It can see and explain the state of the platform, but it does not change it and will not do so by the end of this chapter. The next section follows a request from the chat window through to a merged pull request and shows which component does the writing and why.

 **Practical reference** :

The Kubernetes actions module used in this step can be found here:

`[github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/4-add-kubernetes-actions](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/4-add-kubernetes-actions)`


## Moving from insight to action

Once the assistant can observe the platform, the natural next question is how a change gets made. This is where conversational interfaces are most often misunderstood, so it deserves an exact answer: in this chapter the assistant never performs the write, and the design is better for it.

Take a developer who asks how to stand up a new service, or why a deployment is unhealthy. The assistant answers from what it can read. Through the catalog actions it finds the right template, explains what that template produces, and states which parameters it expects; through the Kubernetes actions it describes the failing pod and points to the manifest that needs to change. It holds no tool that mutates the cluster or the repository. The developer takes that answer to the Backstage scaffolder and runs the template; the scaffolder, not the assistant, performs the write.

From there, the existing CI/CD and GitOps processes take over. Validations run, approvals are applied, and deployments occur through the same mechanisms the organization already trusts. The conversational interface becomes a guided entry point into the platform rather than a bypass around it.

The template used in this chapter ends with a publish step that creates a branch, commits the generated manifests, and opens a pull request against the components repository. Those manifests are the ConfigMap, Deployment, Service, and horizontal pod autoscaler shown earlier in  *Figure 5.6* . Once the pull request is merged, the Argo CD `ApplicationSet` detects the new directory and deploys it, which is the state captured in  *Figure 5.7* . The developer expressed intent in conversation; the platform produced a reviewable change; the controller reconciled the cluster.

This closes the loop the chapter opened with. A Kubernetes Operator receives intent as a custom resource, applies operational knowledge, and reconciles the cluster toward the state that resource describes. The conversational layer performs the user-facing half of the same pattern, and the mapping remains approximate: the prompt expresses intent, the pull request proposes a desired-state change, and the GitOps controller reconciles that change only after it is approved and merged. The conversational interface changes how intent is expressed; it does not change how change reaches production.

Keeping the write path in the template rather than in the assistant is a deliberate choice, and it is why the refusal in *Figure 5.11* is the correct behavior rather than a gap to be closed. The template is reviewed, versioned, and parameterized; its output is predictable. An assistant with direct write access to the cluster would not provide the same reviewability or predictability. *[Chapter 7](https://learning.oreilly.com/library/view/agentic-ai-for/9781806386659/Chapter_7.xhtml#h1_142)* revisits this boundary and gives an agent a genuine mutation tool, but it does so by exposing a single narrowly scoped action that can only open a pull request, never by writing to the cluster directly.

 **Practical reference** : the Backstage template that generates these manifests and opens the pull request, together with the Argo CD `ApplicationSet` that deploys the result, is available at:

`[github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/1-backstage-setup](https://github.com/PacktPublishing/Agentic-AI-for-Platform-Engineering/tree/main/chapter-05/1-backstage-setup)`

This progression demonstrates how conversational interfaces fit naturally into platform engineering when introduced incrementally. Starting from a standard Backstage and GitOps setup, we add conversational capabilities, enrich them with organizational knowledge, extend them with real-time platform awareness, and finally enable them to propose governed changes. The result is not a replacement for platform workflows, but an intuitive layer on top of them that makes the platform easier to understand, safer to operate, and more accessible to developers.

## 💡 讀者實戰筆記：本地環境搭建與真實驗證紀錄（Lab 1 ~ Lab 4 全流程）

為了徹底驗證書中「意圖驅動、GitOps 落地、MCP 唯讀洞察」的架構哲學，我們在本地環境進行了端到端的實機搭建與真實呼叫驗證：

```mermaid
flowchart TD
    subgraph Clients["客戶端（兩種途徑）"]
        Chat["途徑 1：Backstage Chat Assistant<br/>(前端聊天視窗 /assistant/general)"]
        External["途徑 2：外部 MCP 客戶端 / CLI<br/>(Streamable HTTP JSON-RPC :7007)"]
    end

    subgraph BackstageBackend["Backstage Backend (:7007)"]
        Registry["Backstage Actions Registry<br/>(@backstage/plugin-mcp-actions-backend)"]
        Module["Kubectl Actions Module<br/>(kubectl-mcp-actions.ts)"]
        CatalogAct["Catalog Core Actions<br/>(search-catalog / get-catalog-entity)"]
        LangGraphAgent["LangGraph React Agent<br/>(@aws/genai-plugin-langgraph-agent)"]
    end

    subgraph LLMProvider["本機推論引擎 (:11434)"]
        Ollama["Local Ollama<br/>qwen2.5:7b (原生支援 Tool Calling)"]
    end

    subgraph Cluster["Kubernetes (kind: agentic-platform)"]
        K8s["kubectl binary<br/>(Pods, Deployments, Services, Describe)"]
        Argo["ArgoCD v3.0.21<br/>(ApplicationSet: backstage-app-discovery)"]
        MyFirstApp["my-first-app<br/>(2 Pods + Service + HPA)"]
    end

    subgraph GitRepository["Git 儲存庫 (GitHub)"]
        Repo["tedmax100/backstage-components<br/>(main 分支 / PR #1)"]
    end

    Chat -->|程序內調用| LangGraphAgent
    LangGraphAgent <-->|ChatOllama| Ollama
    LangGraphAgent -->|查詢工具| Registry
    Registry --> Module
    Registry --> CatalogAct
    Module -->|執行查詢| K8s
    External -->|HTTP POST /api/mcp-actions/v1| Registry

    Chat -.->|Scaffolder 填表| Repo
    Repo -->|自動偵測| Argo
    Argo -->|GitOps 同步部署| MyFirstApp
```

---

### 1. Lab 1：Backstage 入口網站與 GitOps 自助交付閉環（1-backstage-setup）

#### 嚴苛版本約束與環境初始化
Backstage 演進迅速，新版常伴隨不相容變更。本實驗嚴格遵循生產基準版本：
- **Backstage**：`@backstage/create-app@0.7.9`，所有 `@backstage/*` 套件透過 `package-resolutions.json` 強制鎖定在 `1.48.0`。
- **Runtime**：Node.js v22.19.0，Yarn 4.4.1（透過 Corepack 啟用）。
- **外部儲存庫**：建立公開 GitHub 儲存庫 `tedmax100/backstage-components`，並將具備 PR 權限的 GitHub Token 寫入 `app-config.local.yaml`。

#### 註冊範本與 ArgoCD ApplicationSet
1. 將 `files/webapp-template` 複製至 `my-backstage-app/examples/webapp-template`，並於 `app-config.yaml` 註冊：
```yaml
catalog:
  locations:
    - type: file
      target: ../../examples/webapp-template/template.yaml
      rules:
        - allow: [Template]
    - type: url
      target: https://github.com/tedmax100/backstage-components/blob/main/*/catalog-info.yaml
      rules:
        - allow: [Component]
```
2. 將 `argocd-applicationset.yaml` 內的帳號替換為 `tedmax100` 並套用至叢集 `argocd` 命名空間。其透過 Git 檔案產生器自動監聽 `*/argocd/application.yaml`。

#### 端到端實操驗證
1. 啟動 Backstage：`NODE_OPTIONS=--no-node-snapshot yarn start`。
2. 訪問 `http://localhost:3000/create`，選擇 **Web App with Kubernetes Deployment** 範本。
3. 填入參數：`name: my-first-app`、`namespace: my-first-app`、`repoOwner: tedmax100`、`repoName: backstage-components`。
4. Backstage 後端自動渲染出 9 個檔案，並透過 GitHub API 自動建立 Pull Request `#1 (feat: Add my-first-app)`。
5. 審核並合併 PR 後，ArgoCD ApplicationSet 自動觸發調諧。

#### 踩坑提醒（ArgoCD 部署與快取同步）：
- **命名空間對齊**：若表單未變更 namespace，預設會產生 `namespace: default`，這會與 ApplicationSet 宣告的目標命名空間 `{{path[0]}}` (`my-first-app`) 產生衝突。合併前務必確認清單內的 namespace 一致。
- **Repo-Server 快取清除**：ArgoCD 預設輪詢間隔為 3 分鐘，且 `argocd-repo-server` 會在 Redis 中快取 Git 目錄。若合併後欲立即生效，可連線至 `argocd-redis` 執行 `redis-cli -a <PASSWORD> flushall` 並重啟 `argocd-applicationset-controller`。

#### 真實部署驗證：
```bash
$ kubectl get all,cm,hpa -n my-first-app
```
```text
NAME                                READY   STATUS    RESTARTS   AGE
pod/my-first-app-6b4f5594b6-c6h26   1/1     Running   0          93s
pod/my-first-app-6b4f5594b6-tvwrh   1/1     Running   0          93s

NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/my-first-app   ClusterIP   10.96.132.107   <none>        80/TCP    93s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-first-app   2/2     2            2           93s

NAME                                                   REFERENCE                 TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
horizontalpodautoscaler.autoscaling/my-first-app-hpa   Deployment/my-first-app   cpu: <unknown>/70%   2         10        2          93s
```
內部端點驗證成功回傳：
```html
<div class="container">
  <h1>my-first-app</h1>
  <p>My first Backstage-deployed app</p>
  <p><strong>Namespace:</strong> my-first-app</p>
  <p><strong>Owner:</strong> user:guest</p>
</div>
```

---

### 2. Lab 2：整合 AI 對話助理與本地 Ollama（2-add-chat-assistant）

#### 外掛相依性與架構接合
- **後端外掛**：
  ```bash
  yarn workspace backend add \
    @aws/genai-plugin-for-backstage-backend \
    @aws/genai-plugin-langgraph-agent-for-backstage \
    @backstage/plugin-mcp-actions-backend
  ```
- **前端外掛**：
  ```bash
  yarn workspace app add @aws/genai-plugin-for-backstage
  ```
- **後端註冊順序至關重要**（`packages/backend/src/index.ts`）：
  `mcp-actions-backend` 必須註冊於 `aws-genai` **之前**，因為 GenAI 外掛的啟動生命週期鉤子需要解析 `alpha.core.actionsRegistry` 服務參照：
  ```typescript
  // 必須置於 aws-genai 之前
  backend.add(import('@backstage/plugin-mcp-actions-backend'));
  backend.add(import('@aws/genai-plugin-for-backstage-backend'));
  backend.add(import('@aws/genai-plugin-langgraph-agent-for-backstage'));
  ```

#### 本地 Ollama 模型直連（零雲端 API 依賴）
不同於原書依賴 AWS Bedrock，我們利用 `@aws/genai-plugin-langgraph-agent-for-backstage` 內建的 Ollama 整合能力，在 `app-config.yaml` 配置本機運行的 `qwen2.5:7b`：
```yaml
genai:
  agents:
    general:
      description: General chat assistant
      prompt: >
        You are an expert in platform engineering and answer questions in a succinct and easy to understand manner.
        Answers should always be well-structured and use well-formed Markdown.
        The current user is {username} and you can provide that information if asked.
      langgraph:
        messagesMaxTokens: 32000
        ollama:
          model: 'qwen2.5:7b'
          baseUrl: 'http://127.0.0.1:11434'
```

#### 前端介面與實機測試：
- 在 `packages/app/src/App.tsx` 註冊 `<Route path="/assistant/:agentName" element={<AgentChatPage />} />`。
- 在 `packages/app/src/components/Root/Root.tsx` 側邊欄掛載 `Chat Assistant`。
- 向助理提問："What is Backstage and how does it help platform engineering?"。
- 模型成功透過 LangGraph 代理串流輸出條理清晰的 Markdown 架構解釋。
- **當前邊界確認**：此階段助理僅具備通用程式與雲原生知識，尚未被賦予存取目錄或叢集的工具，無法回答「我們系統有哪些服務？」。

---

### 3. Lab 3：掛載 Backstage Catalog Actions 注入組織靜態結構（3-add-catalog-actions）

#### 啟用目錄動作來源
在 `app-config.yaml` 啟用動作註冊來源並將目錄工具指派給代理：
```yaml
backend:
  actions:
    pluginSources:
      - 'catalog'      # 啟用 Backstage 目錄原生動作
      - 'aws-genai'    # 啟用 GenAI 核心動作

genai:
  registerCoreActions: true
  agents:
    general:
      actions:
        - get-catalog-entity  # 取得特定實體
        - search-catalog      # 跨目錄全文檢索
        - search-techdocs     # 搜尋技術文檔
```

#### 實測問答與「零幻覺」底層原理解密
提問實測：
```text
User: "Find all services owned by guest"
Assistant: "It appears that there are no services currently owned by guest in the catalog.
Would you like to perform another search or check for other types of entities?"
```

#### 為什麼回傳「找不到」反而證明了系統的嚴謹性？
查看後端即時日誌：
```text
search info Search request received: term="service AND owner:guest", filters={"kind":"service"}
POST /api/aws-genai/.backstage/actions/v1/actions/aws-genai:search-catalog/invoke 200 90
```
- **真實工具調用**：模型確實自動呼叫了 `aws-genai:search-catalog` 工具。
- **嚴格基於事實**：在 Backstage 的資料模型規範中，實體的類別（`kind`）只有 `Component`、`API`、`System`、`Template`，根本沒有 `kind: service`。Lab 1 部署的 `my-first-app` 實際定義為 `kind: Component, spec.type: website`。
- **拒絕憑空捏造**：模型嚴格依據檢索到的空結果誠實回答，展現了 Grounded AI（有憑有據的 AI）的核心特徵。當改為提問 `What components do we have in the catalog?` 時，助理隨即精確列出了 `my-first-app` 與 `example-website`。

---

### 4. Lab 4：掛載 Kubernetes MCP Actions 洞察活體運行真相（4-add-kubernetes-actions）

#### 實作 Kubectl 動作模組
1. 安裝 Schema 驗證套件：`yarn workspace backend add zod`。
2. 建立 `packages/backend/src/modules/kubectl-mcp-actions.ts`，向 Actions Registry 註冊 4 個唯讀動作：
   - `kubectl_get_pods`：取得指定命名空間的 Pod 清單（JSON）。
   - `kubectl_get_deployments`：取得 Deployments 清單。
   - `kubectl_get_services`：取得 Services 清單。
   - `kubectl_describe_pod`：取得特定 Pod 的詳細診斷資訊。
3. 於 `packages/backend/src/index.ts` 註冊模組：
   ```typescript
   backend.add(import('./modules/kubectl-mcp-actions'));
   ```
4. 於 `app-config.yaml` 指派動作：
   ```yaml
   backend:
     actions:
       pluginSources:
         - 'catalog'
         - 'aws-genai'
         - 'mcp-actions'

   genai:
     agents:
       general:
         actions:
           - get-catalog-entity
           - search-catalog
           - search-techdocs
           - kubectl_get_pods
           - kubectl_get_deployments
           - kubectl_get_services
           - kubectl_describe_pod
   ```

#### 雙重存取機制（Two Doors, Same Contract）驗證
Backstage MCP Actions 後端將註冊的動作同時暴露為兩種介面：
1. **途徑 1：內部程序內調用**：前端聊天助理透過 LangGraph 直接在 Node.js 程序內部調用。
2. **途徑 2：外部 HTTP MCP 客戶端**：外部 Agent 或 CLI 可透過標準 MCP 協議訪問 `http://localhost:7007/api/mcp-actions/v1`。

#### 外部 MCP 客戶端呼叫實測（HTTP JSON-RPC 2.0）：
```bash
# 實機調用 kubectl_get_pods 查詢 my-first-app
curl -s -X POST http://localhost:7007/api/mcp-actions/v1 \
  -H "Authorization: Bearer test-mcp-client-token-secret-123456" \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"kubectl_get_pods","arguments":{"namespace":"my-first-app"}}}'
```
成功接收到叢集 live 回傳的 `my-first-app-6b4f5594b6-c6h26` 完整 Pod 定義！

#### 跨章節神作聯動：真實活體排障診斷驗證
在聊天視窗中詢問第四章留下的故障情境：
```text
User: "What pods are in the broken-demo namespace, and why are they not healthy?"
```

AI 助理即時回覆：
```text
The pod named payment-processor-8669f87785-zrfjk in the broken-demo namespace is not healthy 
because it is in a CrashLoopBackOff state.

Key details:
- Pod Name: payment-processor-8669f87785-zrfjk
- State: Terminated with exit code 1
- Error Message: The container command is set to:
  echo 'connecting to database...'; sleep 2; echo 'connection timed out'; exit 1
  This indicates the container timed out trying to connect to a database.
```
**驗證收穫**：AI 助理自動呼叫了 `kubectl_describe_pod`，精準讀取了 Pod 內部的具體啟動參數與錯誤碼，並在幾秒鐘內給出根本原因分析！

---

### 💡 結論：對話式介面的架構防線

1. **對話層是 GitOps 的親和介面，絕非直接寫入的後門**：
   變更必須始終保持為「受控的 Pull Request 提案」，交由人類審查與 GitOps 控制器同步，嚴禁賦予對話視窗直接 `kubectl apply` 的危險寫入權限。
2. **MCP 是模型的「感官神經」**：
   藉由 MCP Actions Registry，我們在維持最小權限原則（唯讀工具）的前提下，賦予了本地開源模型深度洞察線上叢集運行真相的超能力。

# Limitations of current AI tools in platform engineering

Despite the benefits shown in the previous sections, current AI tools still face important limitations when applied to platform engineering. These systems are highly effective at generating code and configurations, but they do not inherently understand how a specific platform is designed, governed, or operating at any given moment. Without careful integration, AI-driven interactions can produce results that look correct but fail to align with organizational expectations or current platform conditions.

Six limitations are especially relevant in practice: gaps in platform-specific knowledge, the absence of real-time state awareness, hallucination and the approval processes that mitigate it, the complexity of orchestrating multiple agents, the non-determinism of model output, and the cost and latency of running these systems at scale.

## Organizational and platform-specific knowledge

General-purpose AI models do not come with built-in awareness of an organization's internal standards, golden paths, or architectural decisions. They may understand how to define a Kubernetes Deployment or a Terraform resource, but they do not know which annotations are mandatory, how services are expected to be named, which modules are approved, or how ownership and responsibility are modeled in the platform.

When this organizational knowledge is missing, AI-generated outputs often appear valid but subtly diverge from platform standards. Required metadata may be omitted, outdated patterns may be reused, or definitions may conflict with existing automation. Over time, these inconsistencies can fragment the platform rather than reinforce its intended design.

This limitation is closely tied to hallucination. An AI system may confidently generate configurations or references that do not exist within the organization, especially when it lacks access to authoritative sources. Grounding conversational interfaces in curated organizational knowledge and connecting them to authoritative systems through controlled actions are important safeguards for AI-assisted platform workflows. RAG and MCP are two mechanisms that can support those goals.

## Challenges with real-time platform state awareness

In addition to lacking organizational context, AI tools also lack inherent visibility into the live state of the platform. A model cannot know which workloads are currently running, which environments are healthy, or whether a resource already exists unless it is explicitly connected to the systems that manage that information.

This limitation becomes critical when AI is used to suggest changes. A conversational interface may propose updates that conflict with the current environment, assume resources that no longer exist, or overlook conditions such as partial outages or ongoing rollouts. Even well-structured configurations can become problematic if they are based on stale or incomplete assumptions.

Connecting conversational interfaces to authoritative systems through controlled actions helps address this gap. MCP can standardize that access for external clients, but real-time awareness must still be deliberate, controlled, and observable. Without it, AI-assisted changes risk being disconnected from the reality of how the platform is operating.

## Hallucination, governance, and the role of approval processes

Hallucination remains a fundamental limitation of current AI systems. In platform engineering, the cost of an incorrect assumption is often high, affecting reliability, security, or compliance. For this reason, preserving existing approval and validation processes is not a temporary safeguard but a core design choice.

Routing AI-generated changes through pull requests, reviews, automated checks, and deployment gates helps catch hallucinations before they reach production. These workflows provide both human and automated oversight and make AI an accelerator of safe change rather than an uncontrolled actor.

Conversational interfaces should therefore complement governance, not replace it. They are most effective when they help teams arrive at better proposals faster, while leaving final validation to the same mechanisms already trusted by the platform.

## The complexity of orchestrating multiple agents

As conversational systems evolve, they often expand into multiple specialized agents operating at different stages: retrieving knowledge, interpreting intent, validating configurations, querying platform state, or proposing changes. Over time, orchestrating these agents begins to resemble the architectural challenges seen in the transition from monolithic applications to microservices.

While specialization brings flexibility, it also introduces coordination complexity. Failures become harder to trace, responsibilities can blur, and system behavior can become opaque if boundaries are not clearly defined. Frameworks such as Strands, an open-source SDK from AWS for building agents that reason in a loop over a defined set of tools, help address this by structuring how reasoning, actions, and tool interactions are sequenced and connected over time, making multi-step workflows more predictable and observable. We return to Strands in detail in  *[Chapter 7](https://learning.oreilly.com/library/view/agentic-ai-for/9781806386659/Chapter_7.xhtml#h1_142)* , where it runs the operational agent. MCP complements this approach by providing structured interfaces and controlled actions between components, but neither eliminates the need for careful system design. Platform teams must still define clear boundaries, ownership, and lifecycle rules to prevent agent workflows from becoming fragile or difficult to reason about.

Platform teams must treat agents as first-class architectural elements, with clear ownership, observability, and limits. Otherwise, the complexity introduced by orchestration can undermine the very productivity gains AI promises to deliver.

## Non-determinism and the problem of testing

Every limitation described so far concerns what the assistant knows. This one concerns whether it behaves the same way twice. The same prompt, against the same catalog and the same cluster, can produce different wording, a different sequence of tool calls, or a different conclusion. For a conversational tool, that is often harmless. For a platform capability that engineers are told to rely on, it is a real operational problem.

The difficulty is that the usual safeguard does not apply cleanly. A platform team can regression-test a Terraform module or a scaffolder template because the output is deterministic and comparable. There is no equivalent assertion for "the assistant answered this correctly." Teams that take this seriously build an evaluation set, commonly called an eval: a fixed collection of questions with known-good answers, scored on every change before anything reaches developers, the same way they would gate any other platform change.

This matters most at upgrade time. Model versions are deprecated and replaced on the provider's schedule, not yours, and a newer model is not automatically better at your specific tasks. Without an evaluation set, a platform team has no way to detect that a model change quietly degraded the answers their developers depend on. Pinning the model version, as this chapter's configuration does, is the minimum; knowing what a change to that pin does is the actual requirement.

## Cost and latency at scale

The demo in this chapter is inexpensive because it is small. A production deployment changes that arithmetic in two ways that are easy to underestimate. Retrieval over a large catalog can put more context into a request, and multi-step tool use can trigger several model calls before the assistant answers. Both can increase token usage and therefore inference cost, depending on the model provider and architecture.

Latency is the more immediate risk to adoption. A developer will forgive an assistant that is occasionally wrong far sooner than one that takes fifteen seconds to answer a question they could have answered themselves by opening the catalog. Multi-step tool chains are a common cause, since each round trip can add another model call. Keeping the action set small and specific, as we did here, is as much a performance decision as a safety one.

# The case for embedded knowledge structures

The limitations in the previous section share a single root cause. A model does not know your platform. Every capability added in this chapter was, in effect, a way of giving it access to knowledge that already existed somewhere in the organization. That observation is worth stating directly, because it changes how a platform team should think about preparing for AI.

The assistant became useful at the exact moment it was connected to structures the platform team had already built for entirely different reasons. Nobody maintains a Backstage catalog in order to make a language model smarter; they maintain it so that developers can find services and know who owns them. Nobody adopts GitOps to improve AI outcomes; they adopt it for auditability and rollback. Yet both turned out to be precisely what the assistant needed.


## Why GitOps and Backstage work so well as grounding

Both systems can provide structured, current, and authoritative sources of truth when they are maintained through normal platform workflows.

* The Backstage catalog is a typed model of the organization. Components, systems, APIs, owners, and lifecycle stages are explicit fields, not prose to be interpreted. An assistant querying it does not have to guess who owns a service.
* TechDocs can keep documentation beside the code it describes, allowing the documentation to move with the code. Documentation that drifts is worse than no documentation for grounding because it produces confident but wrong answers.
* Git holds the desired state of environments managed through GitOps, with full history and attribution. The question "what should be running" has a precise answer that does not depend on anyone remembering.
* The GitOps controller continuously reconciles that desired state against the cluster, so the gap between intent and reality is itself observable.

Together, these give an assistant something a general-purpose model can never have: a current, machine-readable account of how this particular organization builds and runs software. Crucially, they also come with governance already attached. The catalog has owners, Git-based workflows have reviewers, and the controller has a reconciliation loop. An assistant built on top of them can reuse much of that governance instead of requiring an AI governance model to be designed from scratch.

## What an ideal embedded system looks like

Extrapolating from the demo, the shape of a mature embedded system becomes fairly clear. It is not a separate AI product bolted onto the platform. It is a capability that reads from the platform's existing sources of truth and writes back through the platform's existing change process.

Such a system would ground every answer in the catalog, the documentation, and live cluster state, and it would say so, citing which entity or which manifest an answer came from, so a developer can verify it. It would expose capabilities as narrow, explicitly registered actions rather than open-ended access, and it would carry the requesting developer's identity into every call so that existing permissions continue to apply. Any change it proposed would arrive as a pull request, subject to the same checks and reviewers as a change written by hand. And it would be observable: which actions ran, on whose behalf, and with what result.

None of those properties are AI features. They are platform engineering properties, which is exactly the point. The organizations best positioned to adopt conversational interfaces are not the ones with the most AI expertise; they are the ones whose platforms are already well structured.

## What this means for platform teams

The practical conclusion is encouraging. If your catalog is accurate, your documentation lives with your code, and your changes flow through Git, most of the work of preparing for conversational interfaces is already done, and the remaining work is integration. If those foundations are weak, adding an assistant will not compensate; it will surface the weakness faster and more publicly, because developers will ask it questions the platform cannot answer.

For developers, the benefit is a lower barrier to the paved road. Finding the right template or the right owner stops requiring knowledge of where to look. For platform teams, the benefit is leverage: the catalog entry written once is now answering questions continuously, and the effort spent on structure pays back through a channel that did not exist when the structure was created. That is the strongest argument for treating embedded knowledge structures as a strong foundation for AI in platform engineering rather than as an afterthought.

# Summary

This chapter followed a single idea from theory into a running system: that intent, expressed in natural language, can become a governed platform change without going around any of the controls a platform team already depends on.

You started from a platform baseline that had no AI in it at all: Backstage as the developer portal, Git as the record of desired state, and Argo CD reconciling the cluster against that record. You then added a chat assistant and watched it fail to answer the questions that mattered, because a model on its own knows nothing about your organization. Closing that gap took two steps: catalog and TechDocs actions gave the assistant your declared platform structure, and read-only Kubernetes actions, registered in the same registry, gave it the live state of the cluster.

You can now describe that progression precisely. You have seen why a general-purpose assistant is not a platform assistant, how a registered action turns a model's request into a narrowly scoped and auditable call, how the same registration is published as an MCP tool for clients outside the portal, and why the assistant's refusal to edit a deployment is a design outcome rather than a defect. You have also seen the shape of the limitations that remain: missing organizational knowledge, stale views of runtime state, hallucination, orchestration complexity, non-determinism, and cost.

The framing that opened the chapter holds all the way through. A Kubernetes Operator receives intent, applies encoded knowledge, and reconciles the cluster toward a desired state. The conversational layer built here does the user-facing half of that same loop: the prompt carries intent, the pull request records desired state, and Argo CD performs the reconciliation. The assistant never becomes the deployment authority; it becomes the most approachable way to reach one.

That boundary is also the starting point for what follows. Everything here was observational or proposal-based, and a human merged every change. The next chapter takes up agentic AI and autonomous behavior, where systems plan across multiple steps, keep memory between them, and act with far less human involvement, and where the governance questions raised here stop being theoretical.

# Further reading

If you want to go deeper into the components used in this chapter, the following sources are the ones we relied on while building the demo:

* **Model Context Protocol specification** – the primitives, transport, and security model behind the MCP endpoint that the actions registry exposes, and behind the servers built in *[Chapter 4](https://learning.oreilly.com/library/view/agentic-ai-for/9781806386659/Chapter_4.xhtml#h1_79)* and in  *[Chapter 7](https://learning.oreilly.com/library/view/agentic-ai-for/9781806386659/Chapter_7.xhtml#h1_142)* : [https://modelcontextprotocol.io](https://modelcontextprotocol.io/)
* **Backstage software catalog documentation** – how entities, ownership, and TechDocs are modeled: [https://backstage.io/docs/features/software-catalog](https://backstage.io/docs/features/software-catalog)
* **Argo CD ****ApplicationSet**** documentation** – the generator pattern that discovers new applications in the components repository: [https://argo-cd.readthedocs.io/en/stable/user-guide/application-set](https://argo-cd.readthedocs.io/en/stable/user-guide/application-set)
* **GenAI plugins for Backstage** – the AWS-maintained plugin suite that provides the chat interface: [https://github.com/awslabs/backstage-plugins-for-aws](https://github.com/awslabs/backstage-plugins-for-aws)
