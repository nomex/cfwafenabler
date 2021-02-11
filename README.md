# cfwafenabler

CloudFlare doesn't allow to set their entire WAF in Simulate mode. Instead, they suggest you to use the API.
cfwafenabler allows you to mass-modify all the rules to put your WAF in Simulate mode

# Installation

To install cfwafenabler just use [pipx](https://github.com/pipxproject/pipx)
```
pipx install cfwafenabler
```

# Usage

Before executing cfwafenabler, you need to set some CloudFlare environment variables.
If you use API key ( global permissions ) you need to set:

```
export CF_API_EMAIL=your@email.com
export CF_API_KEY=YouApiKey
```

If you are using CloudFlare API tokens, you only need to set (it's the same env variable, they reuse it):
```
export CF_API_KEY=YouApiToken
```
This token needs the following permissions:
```
Zone.Zone:Read, Zone.Firewall Services:Edit
```

# Credits

Based in [canozokur's](https://github.com/canozokur/cloudflare-waf-simulate) work.

This package was created with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [byt3bl33d3r/pythoncookie](https://github.com/byt3bl33d3r/pythoncookie) project template.
