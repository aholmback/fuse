from fuse.components import Component

class Deployment(Component):

    def tier_identifiers(self, payload, pinboard, prompt):
        self.context['tier_identifiers'] = prompt(
                text="Comma-separated list of environments that your project will live in",
                validators=["comma_separated_identifiers"],
                )

        pinboard.post(
                'deployment_tiers',
                self.context['tier_identifiers'].split(','),
                position=pinboard.FIRST,
                )

