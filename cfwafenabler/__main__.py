import logging
import sys
import os
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


def setRule(cf,mode,ZONE_ID,WAF_ID,_id,_data,rule):
    try:
        cf.zones.firewall.waf.packages.rules.patch(ZONE_ID, WAF_ID, _id, data=_data)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        log.error('Error: RuleID {}: {}'.format(_id, e))
        log.error(json.dumps(rule, indent=4))


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
            _data = {'mode': mode}
            _description = rule['description']
            _current_mode = rule['mode']
            if 'default_mode' in rule:
                _default_mode = rule['default_mode']

            if mode not in rule['allowed_modes']:
                log.warning('{} mode is not available for rule {}'.format(mode,_id))
                continue

            if rule['default_mode'] == 'disable':
                if rule['mode'] == 'disable':
                    log.info('Rule {} is disabled by default. Not doing anything'.format(_id))
                    continue
                else:
                    log.info('Rule {} is disabled by default. Setting as disabled'.format(_id))
                    _data = {'mode': 'disable'} 
                    setRule(cf,mode,ZONE_ID,WAF_ID,_id,_data,rule)
                    continue

            if rule['mode'] == mode:
                log.info('Rule {} is already in {} mode'.format(_id,mode))
                continue


            log.info('{} mode is available, changing {} to {} mode'.format(mode,_id,mode))
            setRule(cf,mode,ZONE_ID,WAF_ID,_id,_data,rule)

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

def usage():
    log.error('You need to set CF_API_KEY environment variable to run cfwafenabler.')
    log.error('Instructions available in https://github.com/nomex/cfwafenabler')

def main():

    if os.getenv("CF_API_KEY"):
        CF_API_KEY = os.getenv("CF_API_KEY")
        if os.getenv("CF_API_EMAIL"):
            CF_API_EMAIL = os.getenv("CF_API_EMAIL")
            cf = CloudFlare.CloudFlare(token=CF_API_KEY,email=CF_API_EMAIL,raw=True)
        else:
            cf = CloudFlare.CloudFlare(token=CF_API_KEY,raw=True)
    else:
        usage()
        sys.exit(1)



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