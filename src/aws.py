from aws_embedded_metrics import MetricsLogger, metric_scope
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
import energypylinear as epl

tracer = Tracer()


@tracer.capture_lambda_handler  # type: ignore
@metric_scope
def lambda_handler(event, _context: LambdaContext, metrics: MetricsLogger):
    return optimise(event)


def extract_data_type(data, data_type):
    named_objects = [d for d in data if data_type in d]
    if named_objects:
        return named_objects[0][data_type]
    return None


def extract_values(data):
    values = [entry["value"] for entry in data]
    return values


def optimise(event):
    energy_prices = extract_data_type(event, 'energyPrices')
    energy_usage = extract_values(extract_data_type(event, 'energyUsage'))
    solar_forecast = extract_values(extract_data_type(event, 'solarForecast'))
    # site_info = extract_value(event, 'siteInfo')

    site = epl.Site(
        assets=[
            epl.Battery(
                power_mw=2.6,  # site_info['inverter_max_power'],
                capacity_mwh=5.2,  # site_info['battery_capacity'],
                initial_charge_mwh=0.0  # site_info['battery_initial_charge'],
            ),
            epl.RenewableGenerator(
                electric_generation_mwh=solar_forecast,
                name='solar',
            ),
        ],
        electricity_prices=extract_values(energy_prices['import']),
        export_electricity_prices=extract_values(energy_prices['export']),
        electric_load_mwh=energy_usage,
        freq_mins=30,
    )
    simulation = site.optimize(verbose=False)
    return simulation.results.to_json()
