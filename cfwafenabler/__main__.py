import logging
import CloudFlare
import json
from simple_term_menu import TerminalMenu


handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        style="{",
        fmt="[{name}:{filename}] {levelname} - {message}"
    )
)

log = logging.getLogger("cfwafenabler")
log.setLevel(logging.INFO)
log.addHandler(handler)

def getzoneid(cf):
    cf_zones = cf.zones.get()
    zones = []
    zones_ids = []
    for zone in cf_zones['result']:
        zones.append(zone['name'])
        zones_ids.append(zone['id'])
    title = "  Select domain:"
    terminal_menu = TerminalMenu(title=title,menu_entries=zones)
    menu_entry = terminal_menu.show()
    return zones_ids[menu_entry],zones[menu_entry]


def getwafid(cf,ZONE_ID):
    waf_packages = cf.zones.firewall.waf.packages.get(
                ZONE_ID,
                params={'per_page':10,'page':0})

    for package in waf_packages['result']:
        if package['name'] == 'CloudFlare':
            WAF_ID=package['id']
    return(WAF_ID)


def changeRules(cf,mode,ZONE_ID,WAF_ID): 
    page_number = 0
    while True:
        page_number += 1
        try:
            waf_rules = cf.zones.firewall.waf.packages.rules.get(
                ZONE_ID,
                WAF_ID,
                params={'per_page':5,'page':page_number})
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('%d %s - api call failed' % (e, e))

        total_pages = waf_rules['result_info']['total_pages']

        for rule in waf_rules['result']:
            _id = rule['id']

            if mode not in rule['allowed_modes']:
                log.warning('{} mode is not available for rule {}'.format(mode,_id))
                continue

            if rule['mode'] == mode:
                log.info('Rule {} is already in {} mode'.format(_id,mode))
                continue

            _data = {'mode': mode}
            _description = rule['description']
            _current_mode = rule['mode']
            _default_mode = rule['default_mode']
            log.info('{} mode is available, changing {} to {} mode'.format(mode,_id,mode))
            try:
                cf.zones.firewall.waf.packages.rules.patch(ZONE_ID, WAF_ID, _id, data=_data)
            except CloudFlare.exceptions.CloudFlareAPIError as e:
                log.error('Error: RuleID {}: {}'.format(_id, e))
                log.error(json.dumps(rule, indent=4))

        if page_number == total_pages:
            break

    return

def getMode():
    menu = ['default','disable','simulate','block','challenge']
    title = " Select mode ( All rules will have this mode enabled):"
    terminal_menu = TerminalMenu(title=title,menu_entries=menu)
    menu_entry = terminal_menu.show() 
    return menu[menu_entry]

def areYouSure(mode,ZONE_NAME):
    title = " Are you sure you want to enable '" + mode + "' mode for all rules in " + ZONE_NAME + " domain?:" 
    menu = ['No','Yes']
    terminal_menu = TerminalMenu(title=title,menu_entries=menu)
    menu_entry = terminal_menu.show()
    return menu_entry

def main():
    cf = CloudFlare.CloudFlare(raw=True)

    ZONE_ID,ZONE_NAME=getzoneid(cf)
    WAF_ID=getwafid(cf,ZONE_ID)
    mode=getMode()
    apply=areYouSure(mode,ZONE_NAME)

    if apply == 1:
        log.info('Modifying rules')
        changeRules(cf,mode,ZONE_ID,WAF_ID)  
    else:
        log.info('Not Modifying any rule')
      

    return

if __name__ == '__main__':
    main()